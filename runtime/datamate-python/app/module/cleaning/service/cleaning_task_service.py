import json
import re
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any, Set

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.base_entity import LineageNode, LineageEdge
from app.core.exception import BusinessError, ErrorCodes
from app.module.cleaning.repository import (
    CleaningTaskRepository,
    CleaningResultRepository,
    OperatorInstanceRepository,
)
from app.module.cleaning.schema import (
    CleaningTaskDto,
    CreateCleaningTaskRequest,
    CleaningResultDto,
    CleaningTaskLog,
    OperatorInstanceDto,
    CleaningProcess,
    CleaningTaskStatus,
)
from app.module.cleaning.service.cleaning_task_validator import CleaningTaskValidator
from app.module.cleaning.service.cleaning_task_scheduler import CleaningTaskScheduler
from app.module.shared.common.lineage import LineageService
from app.module.shared.schema.lineage import NodeType, EdgeType

logger = get_logger(__name__)

DATASET_PATH = "/dataset"
FLOW_PATH = "/flow"


class CleaningTaskService:
    """Service for managing cleaning tasks"""

    def __init__(
        self,
        task_repo: CleaningTaskRepository,
        result_repo: CleaningResultRepository,
        operator_instance_repo: OperatorInstanceRepository,
        operator_service,
        scheduler: CleaningTaskScheduler,
        validator: CleaningTaskValidator,
        dataset_service,
        lineage_service: LineageService,
    ):
        self.task_repo = task_repo
        self.result_repo = result_repo
        self.operator_instance_repo = operator_instance_repo
        self.operator_service = operator_service
        self.scheduler = scheduler
        self.validator = validator
        self.dataset_service = dataset_service
        self.lineage_service = lineage_service

    async def get_tasks(
        self,
        db: AsyncSession,
        status: str | None = None,
        keyword: str | None = None,
        page: int | None = None,
        size: int | None = None,
    ) -> List[CleaningTaskDto]:
        """Get cleaning tasks"""
        tasks = await self.task_repo.find_tasks(db, status, keyword, page, size)

        for task in tasks:
            await self._set_process(db, task)

        return tasks

    async def _set_process(self, db: AsyncSession, task: CleaningTaskDto) -> None:
        """Set task progress"""
        completed, failed = await self.result_repo.count_by_instance_id(db, task.id)
        task.progress = CleaningProcess.of(task.file_count or 0, completed, failed)

    async def count_tasks(
        self,
        db: AsyncSession,
        status: str | None = None,
        keyword: str | None = None,
    ) -> int:
        """Count cleaning tasks"""
        tasks = await self.task_repo.find_tasks(db, status, keyword, None, None)
        return len(tasks)

    async def get_task(self, db: AsyncSession, task_id: str) -> CleaningTaskDto:
        """Get task by ID"""
        task = await self.task_repo.find_task_by_id(db, task_id)
        if not task:
            raise BusinessError(ErrorCodes.CLEANING_TASK_NOT_FOUND, task_id)

        await self._set_process(db, task)

        instances = await self.operator_instance_repo.find_operator_by_instance_id(db, task_id)

        # Batch query operators
        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None,
                                                                  is_star=None)
        operator_map = {op.id: op for op in all_operators}

        task.instance = []
        for inst in instances:
            operator = operator_map.get(inst.operator_id)
            if operator:
                task.instance.append(OperatorInstanceDto(
                    id=operator.id,
                    name=operator.name,
                    description=operator.description,
                    inputs=operator.inputs,
                    outputs=operator.outputs,
                    settings=operator.settings,
                    categories=operator.categories,
                ))
            else:
                task.instance.append(OperatorInstanceDto(id=inst.operator_id))

        return task

    async def create_task(
        self,
        db: AsyncSession,
        request: CreateCleaningTaskRequest
    ) -> CleaningTaskDto:
        """Create new cleaning task"""
        if request.instance and request.template_id:
            instances = await self.get_instance_by_template_id(db, request.template_id)
            request.instance = instances

        await self.validator.check_task_name_duplication(db, request.name)
        self.validator.check_input_and_output(request.instance)
        executor_type = self.validator.check_and_get_executor_type(request.instance)

        task_id = str(uuid.uuid4())

        dest_dataset_id = request.dest_dataset_id
        dest_dataset_name = request.dest_dataset_name

        if not dest_dataset_id:
            logger.info(f"Creating new dataset: {dest_dataset_name}, type: {request.dest_dataset_type}")
            dest_dataset_response = await self.dataset_service.create_dataset(
                name=dest_dataset_name,
                dataset_type=request.dest_dataset_type,
                description="",
                status="ACTIVE"
            )
            dest_dataset_id = dest_dataset_response.id
            logger.info(f"Successfully created dataset: {dest_dataset_id}")
        else:
            logger.info(f"Using existing dataset: {dest_dataset_id}")
            dest_dataset_response = await self.dataset_service.get_dataset(dest_dataset_id)

        src_dataset = await self.dataset_service.get_dataset(request.src_dataset_id)
        if not src_dataset:
            raise BusinessError(ErrorCodes.CLEANING_DATASET_NOT_FOUND, request.src_dataset_id)

        task_dto = CleaningTaskDto(
            id=task_id,
            name=request.name,
            description=request.description,
            status=CleaningTaskStatus.PENDING,
            src_dataset_id=request.src_dataset_id,
            src_dataset_name=request.src_dataset_name,
            dest_dataset_id=dest_dataset_id,
            dest_dataset_name=dest_dataset_name,
            before_size=src_dataset.totalSize,
            file_count=src_dataset.fileCount,
            retry_count=-1,
        )

        await self.task_repo.insert_task(db, task_dto)

        await self._add_cleaning_to_graph(src_dataset, task_dto, dest_dataset_response)

        await self.operator_instance_repo.insert_instance(db, task_id, request.instance)

        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None, is_star=None)
        operator_map = {op.id: op for op in all_operators}

        await self.prepare_task(dest_dataset_id, task_id, request.instance, operator_map, executor_type)

        return await self.get_task(db, task_id)

    async def _add_cleaning_to_graph(
        self,
        src_dataset,
        task: CleaningTaskDto,
        dest_dataset,
    ) -> None:
        """
        添加清洗任务到血缘图
        """
        from_node = LineageNode(
            id=src_dataset.id,
            node_type=NodeType.DATASET.value,
            name=src_dataset.name,
            description=src_dataset.description or "",
        )

        to_node = LineageNode(
            id=dest_dataset.id,
            node_type=NodeType.DATASET.value,
            name=dest_dataset.name,
            description=dest_dataset.description or "",
        )

        edge = LineageEdge(
            process_id=task.id,
            name=task.name or "",
            description=task.description or "",
            edge_type=EdgeType.DATA_CLEANING.value,
            from_node_id=from_node.id,
            to_node_id=to_node.id,
        )

        await self.lineage_service.generate_graph(from_node, edge, to_node)

    async def prepare_task(
        self,
        dataset_id: str,
        task_id: str,
        instances: List[OperatorInstanceDto],
        operator_map: dict,
        executor_type: str,
    ) -> None:
        """Prepare task configuration file"""
        process_config = {
            "dataset_id": dataset_id,
            "instance_id": task_id,
            "dataset_path": f"{FLOW_PATH}/{task_id}/dataset.jsonl",
            "export_path": f"{DATASET_PATH}/{dataset_id}",
            "executor_type": executor_type,
            "process": [],
        }

        for instance in instances:
            operator = operator_map.get(instance.id)
            if not operator:
                continue

            operator_config = self._get_default_values(operator)
            operator_config.update(instance.overrides)

            runtime_config = self._get_runtime_config(operator)
            operator_config.update(runtime_config)

            process_config["process"].append({instance.id: operator_config})

        config_file_path = Path(f"{FLOW_PATH}/{task_id}/process.yaml")
        config_file_path.parent.mkdir(parents=True, exist_ok=True)

        import yaml
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(process_config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to write process.yaml: {e}")
            raise BusinessError(ErrorCodes.CLEANING_FILE_SYSTEM_ERROR, str(e))

    def _get_default_values(self, operator) -> Dict[str, Any]:
        """Get default values from operator settings"""
        if not operator.settings:
            return {}

        try:
            settings = json.loads(operator.settings)
            defaults = {}

            for key, value in settings.items():
                setting_type = value.get("type")
                if "defaultVal" in value:
                    defaults[key] = value["defaultVal"]

            return defaults
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse settings: {e}")
            return {}

    def _get_runtime_config(self, operator) -> Dict[str, Any]:
        """Get runtime configuration from operator"""
        if not operator.runtime:
            return {}

        try:
            return json.loads(operator.runtime)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse runtime config: {e}")
            return {}

    async def scan_dataset(
        self,
        db: AsyncSession,
        task_id: str,
        src_dataset_id: str,
        succeed_files: Set[str] | None = None,
    ) -> None:
        """Scan source dataset and create dataset.jsonl"""
        target_file_path = Path(f"{FLOW_PATH}/{task_id}/dataset.jsonl")
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        query = text("""
            SELECT id, file_name, file_path, file_type, file_size
            FROM t_dm_dataset_files
            WHERE dataset_id = :dataset_id
            ORDER BY created_at
        """)

        result = await db.execute(query, {"dataset_id": src_dataset_id})
        files = result.fetchall()

        with open(target_file_path, 'w', encoding='utf-8') as f:
            for file in files:
                if succeed_files and file.id in succeed_files:
                    continue

                file_info = {
                    "fileId": file.id,
                    "fileName": file.file_name,
                    "filePath": file.file_path,
                    "fileType": file.file_type,
                    "fileSize": file.file_size,
                }
                f.write(json.dumps(file_info, ensure_ascii=False) + "\n")

    async def get_task_results(self, db: AsyncSession, task_id: str) -> List[CleaningResultDto]:
        """Get task results"""
        return await self.result_repo.find_by_instance_id(db, task_id)

    async def get_task_log(self, db: AsyncSession, task_id: str, retry_count: int) -> List[CleaningTaskLog]:
        """Get task log"""
        self.validator.check_task_id(task_id)

        log_path = Path(f"{FLOW_PATH}/{task_id}/output.log")
        if retry_count > 0:
            log_path = Path(f"{FLOW_PATH}/{task_id}/output.log.{retry_count}")

        if not log_path.exists():
            return []

        logs = []
        last_level = "INFO"

        standard_level_pattern = re.compile(
            r"\b(DEBUG|Debug|INFO|Info|WARN|Warn|WARNING|Warning|ERROR|Error|FATAL|Fatal)\b"
        )
        exception_suffix_pattern = re.compile(r"\b\w+(Warning|Error|Exception)\b")

        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                last_level = self._get_log_level(line, last_level, standard_level_pattern, exception_suffix_pattern)
                logs.append(CleaningTaskLog(level=last_level, message=line.rstrip()))

        return logs

    def _get_log_level(self, line: str, default_level: str, std_pattern, ex_pattern) -> str:
        """Extract log level from log line"""
        if not line or not line.strip():
            return default_level

        std_match = std_pattern.search(line)
        if std_match:
            return std_match.group(1).upper()

        ex_match = ex_pattern.search(line)
        if ex_match:
            match = ex_match.group(1).upper()
            if match == "WARNING":
                return "WARN"
            if match in ["ERROR", "EXCEPTION"]:
                return "ERROR"

        return default_level

    async def delete_task(self, db: AsyncSession, task_id: str) -> None:
        """Delete task"""
        self.validator.check_task_id(task_id)

        await self.task_repo.delete_task_by_id(db, task_id)
        await self.operator_instance_repo.delete_by_instance_id(db, task_id)
        await self.result_repo.delete_by_instance_id(db, task_id)

        task_path = Path(f"{FLOW_PATH}/{task_id}")
        if task_path.exists():
            try:
                shutil.rmtree(task_path)
            except Exception as e:
                logger.warning(f"Failed to delete task path {task_id}: {e}")

    async def execute_task(self, db: AsyncSession, task_id: str) -> bool:
        """Execute task"""
        succeeded = await self.result_repo.find_by_instance_id(db, task_id, "COMPLETED")
        succeed_set = {res.src_file_id for res in succeeded}

        task = await self.task_repo.find_task_by_id(db, task_id)
        if not task:
            raise BusinessError(ErrorCodes.CLEANING_TASK_NOT_FOUND, task_id)

        await self.scan_dataset(db, task_id, task.src_dataset_id, succeed_set)
        await self.result_repo.delete_by_instance_id(db, task_id, "FAILED")

        return await self.scheduler.execute_task(db, task_id, (task.retry_count or 0) + 1)

    async def stop_task(self, db: AsyncSession, task_id: str) -> bool:
        """Stop task"""
        return await self.scheduler.stop_task(db, task_id)

    async def get_instance_by_template_id(
        self,
        db: AsyncSession,
        template_id: str
    ) -> List[OperatorInstanceDto]:
        """Get instances by template ID (delegated to template service)"""
        instances = await self.operator_instance_repo.find_operator_by_instance_id(db, template_id)

        # Batch query operators
        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None,
                                                                  is_star=None)
        operator_map = {op.id: op for op in all_operators}

        result = []
        for inst in instances:
            operator = operator_map.get(inst.operator_id)
            if operator:
                operator_dto = OperatorInstanceDto(
                    id=operator.id,
                    name=operator.name,
                    description=operator.description,
                    inputs=operator.inputs,
                    outputs=operator.outputs,
                    settings=operator.settings,
                    categories=operator.categories,
                )
                if inst.settings_override:
                    try:
                        operator_dto.overrides = json.loads(inst.settings_override)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse settings for {inst.operator_id}: {e}")
                result.append(operator_dto)

        return result
