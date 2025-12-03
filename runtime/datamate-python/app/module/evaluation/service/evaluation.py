import json
import uuid
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessErrorCodeEnum, BusinessException
from app.core.logging import get_logger
from app.db.models import EvaluationItem, EvaluationTask, DatasetFiles
from app.db.session import AsyncSessionLocal
from app.module.evaluation.schema.evaluation import SourceType
from app.module.shared.schema import TaskStatus
from app.module.shared.util.model_chat import call_openai_style_model
from app.module.evaluation.schema.prompt import get_prompt
from app.module.shared.util.structured_file import StructuredFileHandlerFactory
from app.module.system.service.common_service import get_model_by_id

logger = get_logger(__name__)

class EvaluationExecutor:
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        self.db = db
        self.task = task

    async def save_eval_items(self):
        pass

    def get_eval_prompt(self, item: EvaluationItem) -> str:
        pass

    async def execute(self):
        eval_config = json.loads(self.task.eval_config)
        model_config = await get_model_by_id(self.db, eval_config.get("model_id"))
        offset = 0
        size = 2
        items = (await self.db.execute(
            select(EvaluationItem).where(EvaluationItem.task_id == self.task.id).offset(offset).limit(size)
        )).scalars().all()
        while len(items) > 0:
            for item in items:
                prompt_text = self.get_eval_prompt(item)
                resp_text = await asyncio.to_thread(
                    call_openai_style_model, model_config.base_url, model_config.api_key, model_config.model_name,
                    prompt_text
                )
                item.eval_result = resp_text
                item.status = TaskStatus.COMPLETED.value
            offset += size
            items = (await self.db.execute(
                select(EvaluationItem).where(EvaluationItem.task_id == self.task.id).offset(offset).limit(size)
            )).scalars().all()

    def get_source_type(self) -> SourceType:
        pass


class DatasetEvaluationExecutor(EvaluationExecutor):
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        super().__init__(db, task)

    async def save_eval_items(self):
        dataset_files = (await self.db.execute(select(DatasetFiles)
                                               .where(DatasetFiles.dataset_id == self.task.source_id))).scalars().all()
        handler = StructuredFileHandlerFactory().get_handler(self.task.task_type)
        for dataset_file in dataset_files:
            if dataset_file.file_type.upper() != "JSON" and dataset_file.file_type.upper() != "JSONL":
                continue
            items = handler.get_items_from_file(dataset_file.file_path)
            logger.info(f"parse {len(items)} items from file {dataset_file.file_name}")
            for item in items:
                self.db.add(EvaluationItem(
                    id=str(uuid.uuid4()),
                    task_id=self.task.id,
                    file_id=dataset_file.id,
                    item_id=item.get("id") if item.get("id") else str(uuid.uuid4()),
                    eval_content=json.dumps(item, ensure_ascii=False),
                    status=TaskStatus.PENDING.value,
                ))

    def get_source_type(self) -> SourceType:
        return SourceType.DATASET

    def get_eval_prompt(self, item: EvaluationItem) -> str:
        prompt_text = get_prompt(self.task.task_type, json.loads(self.task.eval_config).get("dimensions"))
        eval_content = json.loads(item.eval_content)
        if self.task.task_type == "QA":
            prompt_text = ((prompt_text.replace("{content}", eval_content.get("input"))
                           .replace("{question}", eval_content.get("instruction")))
                           .replace("{answer}", eval_content.get("output")))
        return prompt_text


class SynthesisEvaluationExecutor(EvaluationExecutor):
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        super().__init__(db, task)

    def save_eval_items(self):
        pass

    def get_source_type(self) -> SourceType:
        return SourceType.SYNTHESIS

    def get_eval_prompt(self, item: EvaluationItem) -> str:
        pass


class EvaluationExecutorFactory:
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        self.db = db
        self.executors: list[EvaluationExecutor] = []
        self.executors.append(DatasetEvaluationExecutor(db, task))
        self.executors.append(SynthesisEvaluationExecutor(db, task))

    def get_executor(self, source_type: str) -> EvaluationExecutor:
        for executor in self.executors:
            if executor.get_source_type().value == source_type:
                return executor
        raise BusinessException(BusinessErrorCodeEnum.TASK_TYPE_ERROR.value)


class EvaluationTaskService:

    @staticmethod
    async def run_evaluation_task(task_id: str):
        """
        Background worker to run evaluations.
        - task_id: id of EvaluationTaskModel
        """
        logger.info(f"Background evaluation worker started add items for task {task_id}")
        async with AsyncSessionLocal() as session:
            try:
                task = await session.execute(select(EvaluationTask).where(EvaluationTask.id == task_id))
                task = task.scalar_one_or_none()
                factory = EvaluationExecutorFactory(session, task)
                executor = factory.get_executor(task.source_type)
                await executor.save_eval_items()
                task.status = TaskStatus.RUNNING.value
            except Exception as e:
                logger.error(f"Background worker encountered error for task {task_id}: {e}")
                task.status = TaskStatus.FAILED.value
            finally:
                await session.commit()

        logger.info(f"Background evaluation worker started for task {task_id}")
        async with AsyncSessionLocal() as session:
            try:
                task = await session.execute(select(EvaluationTask).where(EvaluationTask.id == task_id))
                task = task.scalar_one_or_none()
                factory = EvaluationExecutorFactory(session, task)
                executor = factory.get_executor(task.source_type)
                await executor.execute()
                logger.info(f"Background evaluation worker finished for task {task_id}")
                task.status = TaskStatus.COMPLETED.value
            except Exception as e:
                logger.error(f"Background worker encountered error for task {task_id}: {e}")
                task.status = TaskStatus.FAILED.value
            finally:
                await session.commit()
