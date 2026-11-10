import json
import uuid
import asyncio

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ErrorCodes, BusinessError
from app.core.logging import get_logger
from app.db.models import EvaluationItem, EvaluationTask, DatasetFiles
from app.db.models.data_evaluation import EvaluationFile
from app.db.models.data_synthesis import DataSynthesisFileInstance, SynthesisData
from app.db.session import AsyncSessionLocal
from app.module.evaluation.schema.evaluation import SourceType
from app.module.shared.schema import TaskStatus
from app.module.shared.util.model_chat import call_openai_style_model, extract_json_substring
from app.module.evaluation.schema.prompt import get_prompt
from app.module.shared.util.structured_file import StructuredFileHandlerFactory
from app.module.system.service.common_service import get_model_by_id

logger = get_logger(__name__)

_MAX_EVAL_ATTEMPTS = 3


class EvaluationExecutor:
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        self.db = db
        self.task = task

    async def save_eval_items(self):
        pass

    @staticmethod
    def _as_prompt_text(value) -> str:
        """Render a dataset field as prompt text."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    def get_eval_prompt(self, item: EvaluationItem) -> str:
        prompt_text = get_prompt(self.task.task_type, json.loads(self.task.eval_config).get("dimensions"))
        eval_content = json.loads(item.eval_content or "{}")
        if not isinstance(eval_content, dict):
            logger.warning(
                f"Eval content of item {item.id} is {type(eval_content).__name__}, not an object; "
                "using it as the instruction text"
            )
            eval_content = {"instruction": self._as_prompt_text(eval_content)}
        if self.task.task_type == "QA":
            prompt_text = ((prompt_text.replace("{content}", self._as_prompt_text(eval_content.get("input")))
                            .replace("{question}", self._as_prompt_text(eval_content.get("instruction"))))
                           .replace("{answer}", self._as_prompt_text(eval_content.get("output"))))
        if self.task.task_type == "COT":
            prompt_text = ((prompt_text.replace("{question}", self._as_prompt_text(eval_content.get("instruction")))
                            .replace("{conclusion}", self._as_prompt_text(eval_content.get("output"))))
                           .replace("{chain_of_thought}", self._as_prompt_text(eval_content.get("chain_of_thought"))))
        return prompt_text

    async def execute(self):
        eval_config = json.loads(self.task.eval_config)
        models = await get_model_by_id(self.db, eval_config.get("modelId"))
        semaphore = asyncio.Semaphore(10)
        files = (await self.db.execute(
            select(EvaluationFile).where(EvaluationFile.task_id == self.task.id)
        )).scalars().all()
        query = select(EvaluationItem).where(EvaluationItem.task_id == self.task.id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        if total <= 0:
            logger.error(f"No evaluation items found for task {self.task.id}; aborting evaluation")
            raise BusinessError(ErrorCodes.EVALUATION_NO_ITEMS, data={"task_id": self.task.id})
        evaluated_count = 0
        for file in files:
            items = (await self.db.execute(query.where(EvaluationItem.file_id == file.file_id))).scalars().all()
            tasks = [
                self.evaluate_item(models, item, semaphore)
                for item in items
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for item, result in zip(items, results):
                if isinstance(result, BaseException):
                    logger.error(
                        f"Unexpected error while evaluating task={self.task.id}, item={item.id}: {result!r}"
                    )
                    item.status = TaskStatus.FAILED.value
            completed_count = sum(1 for item in items if item.status == TaskStatus.COMPLETED.value)
            file.evaluated_count = completed_count
            evaluated_count += completed_count
            self.task.eval_process = evaluated_count / total
            await self.db.commit()
        logger.info(
            f"Evaluation finished for task {self.task.id}: {evaluated_count}/{total} items evaluated"
        )
        if evaluated_count == 0:
            logger.error(f"No item could be evaluated for task {self.task.id}; marking it as failed")
            raise BusinessError(
                ErrorCodes.EVALUATION_ALL_ITEMS_FAILED, data={"task_id": self.task.id}
            )

    async def evaluate_item(self, models, item: EvaluationItem, semaphore: asyncio.Semaphore):
        """Evaluate one item and store the outcome on the ORM object.

        The caller owns the transaction: this method never commits, so concurrent
        coroutines cannot race on the single AsyncSession shared by the executor.
        """
        async with semaphore:
            try:
                prompt_text = self.get_eval_prompt(item)
            except Exception as e:
                logger.error(
                    f"Failed to build evaluation prompt for task={self.task.id}, item={item.id}: {e}"
                )
                item.status = TaskStatus.FAILED.value
                return

            for attempt in range(1, _MAX_EVAL_ATTEMPTS + 1):
                try:
                    resp_text = await asyncio.to_thread(
                        call_openai_style_model, models.base_url, models.api_key, models.model_name,
                        prompt_text,
                    )
                except Exception as e:
                    logger.error(
                        f"Model call failed (attempt {attempt}/{_MAX_EVAL_ATTEMPTS}) for task={self.task.id}, "
                        f"file={item.file_id}, item={item.id}: {e}"
                    )
                    continue
                resp_text = extract_json_substring(resp_text)
                try:
                    json.loads(resp_text)
                except Exception as e:
                    logger.error(
                        f"Failed to parse LLM answer as JSON for task={self.task.id}, file={item.file_id}: {e}. Raw answer: {resp_text!r}"
                    )
                    continue
                item.eval_result = resp_text
                item.status = TaskStatus.COMPLETED.value
                return

            logger.warning(
                f"Evaluation gave up after {_MAX_EVAL_ATTEMPTS} attempts for task={self.task.id}, "
                f"file={item.file_id}, item={item.id}"
            )
            item.status = TaskStatus.FAILED.value

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
        parsed_count = 0
        for dataset_file in dataset_files:
            if dataset_file.file_type.upper() != "JSON" and dataset_file.file_type.upper() != "JSONL":
                continue
            items = handler.get_items_from_file(dataset_file.file_path)
            logger.info(f"parse {len(items)} items from file {dataset_file.file_name}")
            if not items:
                logger.warning(
                    f"No valid {self.task.task_type} items parsed from file {dataset_file.file_name} "
                    f"({dataset_file.file_path}); file skipped"
                )
                continue
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
            parsed_count += len(items)
        if parsed_count == 0:
            raise BusinessError(ErrorCodes.EVALUATION_NO_ITEMS, data={"task_id": self.task.id})

    def get_source_type(self) -> SourceType:
        return SourceType.DATASET


class SynthesisEvaluationExecutor(EvaluationExecutor):
    def __init__(self, db: AsyncSession, task: EvaluationTask):
        super().__init__(db, task)

    async def save_eval_items(self):
        synthesis_files = ((await self.db.execute(select(DataSynthesisFileInstance)
                               .where(DataSynthesisFileInstance.synthesis_instance_id == self.task.source_id)))
                           .scalars().all())
        parsed_count = 0
        for synthesis_file in synthesis_files:
            synthesis_datas = ((await self.db.execute(select(SynthesisData)
                                                     .where(SynthesisData.synthesis_file_instance_id == synthesis_file.id)))
                               .scalars().all())
            logger.info(f"get {len(synthesis_datas)} items from file {synthesis_file.file_name}")
            if not synthesis_datas:
                logger.warning(
                    f"No synthesized data found for file {synthesis_file.file_name}; file skipped"
                )
                continue
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
            parsed_count += len(synthesis_datas)
        if parsed_count == 0:
            raise BusinessError(ErrorCodes.EVALUATION_NO_ITEMS, data={"task_id": self.task.id})

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
        raise BusinessError(ErrorCodes.EVALUATION_TASK_TYPE_ERROR)


class EvaluationTaskService:

    @staticmethod
    async def run_evaluation_task(task_id: str):
        """
        Background worker to run evaluations.
        - task_id: id of EvaluationTaskModel
        """
        logger.info(f"Background evaluation worker started add items for task {task_id}")
        items_ready = False
        is_manual = False
        async with AsyncSessionLocal() as session:
            task = None
            try:
                task = await session.execute(select(EvaluationTask).where(EvaluationTask.id == task_id))
                task = task.scalar_one_or_none()
                if task is None:
                    logger.error(f"Evaluation task {task_id} not found, skip background worker")
                    return
                is_manual = task.eval_method == "MANUAL"
                factory = EvaluationExecutorFactory(session, task)
                executor = factory.get_executor(task.source_type)
                await executor.save_eval_items()
                task.eval_process = 0.0
                task.status = TaskStatus.RUNNING.value
                items_ready = True
            except Exception as e:
                logger.error(f"Background worker encountered error for task {task_id}: {e}")
                if task is not None:
                    task.status = TaskStatus.FAILED.value
            finally:
                await session.commit()

        if not items_ready:
            logger.error(f"Skip evaluation for task {task_id} because item preparation failed")
            return

        if is_manual:
            logger.info(f"Manual evaluation task {task_id} is ready for review")
            return

        logger.info(f"Background evaluation worker started for task {task_id}")
        async with AsyncSessionLocal() as session:
            task = None
            try:
                task = await session.execute(select(EvaluationTask).where(EvaluationTask.id == task_id))
                task = task.scalar_one_or_none()
                if task is None:
                    logger.error(f"Evaluation task {task_id} not found, skip background worker")
                    return
                factory = EvaluationExecutorFactory(session, task)
                executor = factory.get_executor(task.source_type)
                await executor.execute()
                logger.info(f"Background evaluation worker finished for task {task_id}")
                task.status = TaskStatus.COMPLETED.value
            except Exception as e:
                logger.error(f"Background worker encountered error for task {task_id}: {e}")
                if task is not None:
                    task.status = TaskStatus.FAILED.value
            finally:
                await session.commit()
