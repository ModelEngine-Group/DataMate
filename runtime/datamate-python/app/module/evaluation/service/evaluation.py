import json
import uuid
import asyncio

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessErrorCodeEnum, BusinessException
from app.core.logging import get_logger
from app.db.models import EvaluationItem, EvaluationTask, DatasetFiles
from app.db.models.data_evaluation import EvaluationFile
from app.db.models.data_synthesis import DataSynthesisFileInstance, SynthesisData
from app.db.session import AsyncSessionLocal
from app.module.evaluation.schema.evaluation import SourceType
from app.module.shared.schema import TaskStatus
from app.module.shared.util.model_chat import call_openai_style_model, _extract_json_substring
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
        prompt_text = get_prompt(self.task.task_type, json.loads(self.task.eval_config).get("dimensions"))
        eval_content = json.loads(item.eval_content)
        if self.task.task_type == "QA":
            prompt_text = ((prompt_text.replace("{content}", eval_content.get("input"))
                            .replace("{question}", eval_content.get("instruction")))
                           .replace("{answer}", eval_content.get("output")))
        if self.task.task_type == "COT":
            prompt_text = ((prompt_text.replace("{question}", eval_content.get("question"))
                            .replace("{conclusion}", eval_content.get("conclusion")))
                           .replace("{chain_of_thought}", eval_content.get("chain_of_thought")))
        return prompt_text

    async def execute(self):
        eval_config = json.loads(self.task.eval_config)
        model_config = await get_model_by_id(self.db, eval_config.get("modelId"))
        semaphore = asyncio.Semaphore(10)
        files = (await self.db.execute(
            select(EvaluationFile).where(EvaluationFile.task_id == self.task.id)
        )).scalars().all()
        query = select(EvaluationItem).where(EvaluationItem.task_id == self.task.id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        evaluated_count = 0
        for file in files:
            items = (await self.db.execute(query.where(EvaluationItem.file_id == file.file_id))).scalars().all()
            tasks = [
                self.evaluate_item(model_config, item, semaphore)
                for item in items
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            file.evaluated_count = len(items)
            evaluated_count += file.evaluated_count
            self.task.eval_process = evaluated_count / total
            await self.db.commit()

    async def evaluate_item(self, model_config, item: EvaluationItem, semaphore: asyncio.Semaphore):
        async with semaphore:
            max_try = 3
            while max_try > 0:
                prompt_text = self.get_eval_prompt(item)
                resp_text = await asyncio.to_thread(
                    call_openai_style_model, model_config.base_url, model_config.api_key, model_config.model_name,
                    prompt_text,
                )
                resp_text = _extract_json_substring(resp_text)
                try:
                    json.loads(resp_text)
                except Exception as e:
                    logger.error(
                        f"Failed to parse LLM answer as JSON for task={self.task.id}, file={item.file_id}: {e}. Raw answer: {resp_text!r}"
                    )
                    max_try -= 1
                    continue
                item.eval_result = resp_text
                item.status = TaskStatus.COMPLETED.value
                await self.db.commit()
                return


    def get_source_type(self) -> SourceType:
        pass


class DatasetEvaluationExecutor(EvaluationExecutor):
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        super().__init__(db, task)

    async def save_eval_items(self):
        dataset_files = ((await self.db.execute(select(DatasetFiles)
                                               .where(DatasetFiles.dataset_id == self.task.source_id)))
                         .scalars().all())
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
                    eval_result="{}",
                    status=TaskStatus.PENDING.value,
                    created_by=self.task.created_by,
                    updated_by=self.task.updated_by,
                ))
            self.db.add(EvaluationFile(
                id=str(uuid.uuid4()),
                task_id=self.task.id,
                file_id=dataset_file.id,
                file_name=dataset_file.file_name,
                total_count=len(items),
                evaluated_count=0,
                created_by=self.task.created_by,
                updated_by=self.task.updated_by,
            ))

    def get_source_type(self) -> SourceType:
        return SourceType.DATASET


class SynthesisEvaluationExecutor(EvaluationExecutor):
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        super().__init__(db, task)

    async def save_eval_items(self):
        synthesis_files = ((await self.db.execute(select(DataSynthesisFileInstance)
                               .where(DataSynthesisFileInstance.synthesis_instance_id == self.task.source_id)))
                           .scalars().all())
        for synthesis_file in synthesis_files:
            synthesis_datas = ((await self.db.execute(select(SynthesisData)
                                                     .where(SynthesisData.synthesis_file_instance_id == synthesis_file.id)))
                               .scalars().all())
            logger.info(f"get {len(synthesis_datas)} items from file {synthesis_file.file_name}")
            for synthesis_data in synthesis_datas:
                self.db.add(EvaluationItem(
                    id=str(uuid.uuid4()),
                    task_id=self.task.id,
                    file_id=synthesis_file.id,
                    item_id=synthesis_data.id,
                    eval_content=json.dumps(synthesis_data.data),
                    eval_result="{}",
                    status=TaskStatus.PENDING.value,
                    created_by=self.task.created_by,
                    updated_by=self.task.updated_by,
                ))
            self.db.add(EvaluationFile(
                id=str(uuid.uuid4()),
                task_id=self.task.id,
                file_id=synthesis_file.id,
                file_name=synthesis_file.file_name,
                total_count=len(synthesis_datas),
                evaluated_count=0,
                created_by=self.task.created_by,
                updated_by=self.task.updated_by,
            ))
        pass

    def get_source_type(self) -> SourceType:
        return SourceType.SYNTHESIS


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
