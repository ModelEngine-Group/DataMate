import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Dataset
from app.db.models.data_collection import CollectionTask, CollectionTemplate
from app.db.session import AsyncSessionLocal
from app.module.collection.client.datax_client import DataxClient
from app.module.collection.schema.collection import SyncMode, create_execute_record
from app.module.collection.scheduler import validate_schedule_expression
from app.module.dataset.service.service import Service
from app.module.shared.schema import TaskStatus, NodeType, EdgeType
from app.module.shared.common.lineage import LineageService
from app.db.models.base_entity import LineageNode, LineageEdge

logger = get_logger(__name__)


@dataclass
class _RuntimeTask:
    id: str
    config: str
    timeout_seconds: int
    sync_mode: str
    status: Optional[str] = None


@dataclass
class _RuntimeExecution:
    id: str
    log_path: str
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    status: Optional[str] = None

class CollectionTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task: CollectionTask, dataset: Dataset) -> CollectionTask:
        self.db.add(task)

        # If it's a one-time task, execute it immediately
        if task.sync_mode == SyncMode.ONCE:
            task.status = TaskStatus.RUNNING.name
            await self.db.commit()
            asyncio.create_task(CollectionTaskService.run_async(task.id, dataset.id if dataset else None))
        elif task.sync_mode == SyncMode.SCHEDULED:
            if not task.schedule_expression:
                raise ValueError("schedule_expression is required for scheduled tasks")
            validate_schedule_expression(task.schedule_expression)
        return task

    @staticmethod
    async def run_async(task_id: str, dataset_id: str = None):
        logger.info(f"start to execute task {task_id}")
        async with AsyncSessionLocal() as session:
            task = await session.execute(select(CollectionTask).where(CollectionTask.id == task_id))
            task = task.scalar_one_or_none()
            if not task:
                logger.error(f"task {task_id} not exist")
                return
            template = await session.execute(select(CollectionTemplate).where(CollectionTemplate.id == task.template_id))
            template = template.scalar_one_or_none()
            if not template:
                logger.error(f"template {task.template_name} not exist")
                return
            task_execution = create_execute_record(task)
            session.add(task_execution)
            await session.commit()
            await asyncio.to_thread(
                DataxClient(execution=task_execution, task=task, template=template).run_datax_job
            )
            await session.commit()
            if dataset_id:
                dataset_service = Service(db=session)
                source_paths = []
                target_path = Path(task.target_path)
                if target_path.exists() and target_path.is_dir():
                    for file_path in target_path.rglob('*'):
                        if file_path.is_file():
                            source_paths.append(str(file_path.absolute()))
                await dataset_service.add_files_to_dataset(dataset_id=dataset_id, source_paths=source_paths)
                await CollectionTaskService._add_dataset_to_graph(
                    session=session,
                    dataset_id=dataset_id,
                    task=task
                )

    @staticmethod
    async def _add_dataset_to_graph(
        session: AsyncSession,
        dataset_id: str,
        task: CollectionTask
    ) -> None:
        """
        在归集完成后，将数据集加入血缘图。
        参考 Java 侧 addDatasetToGraph 逻辑：
        collection(DATASOURCE) -> dataset(DATASET) via DATA_COLLECTION edge
        """
        try:
            dataset = await session.get(Dataset, dataset_id)
            if not dataset:
                logger.warning(f"dataset {dataset_id} not found when building lineage graph")
                return

            dataset_node = LineageNode(
                id=dataset.id,
                node_type=NodeType.DATASET.value,
                name=dataset.name,
                description=dataset.description
            )

            collection_node = LineageNode(
                id=task.id,
                node_type=NodeType.DATASOURCE.value,
                name=task.name,
                description=task.description
            )

            collection_edge = LineageEdge(
                process_id=task.id,
                name=task.name,
                edge_type=EdgeType.DATA_COLLECTION.value,
                description=dataset.description,
                from_node_id=task.id,
                to_node_id=dataset.id
            )

            lineage_service = LineageService(db=session)
            await lineage_service.generate_graph(collection_node, collection_edge, dataset_node)
            await session.commit()
        except Exception as exc:
            logger.error(f"Failed to add dataset lineage graph: {exc}")
            await session.rollback()
