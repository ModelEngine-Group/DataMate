import asyncio
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_collection import CollectionTask, CollectionTemplate
from app.db.session import AsyncSessionLocal
from app.module.collection.client.datax_client import DataxClient
from app.module.collection.schema.collection import SyncMode, create_execute_record
from app.module.shared.schema import TaskStatus

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

    async def create_task(self, task: CollectionTask) -> CollectionTask:
        self.db.add(task)

        # If it's a one-time task, execute it immediately
        if task.sync_mode == SyncMode.ONCE:
            task.status = TaskStatus.RUNNING.name
            await self.db.commit()
            asyncio.create_task(CollectionTaskService.run_async(task.id))
        return task

    @staticmethod
    async def run_async(task_id: str):
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
