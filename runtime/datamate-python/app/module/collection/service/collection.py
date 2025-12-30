import asyncio

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_collection import CollectionTask, CollectionTemplate
from app.db.session import AsyncSessionLocal
from app.module.collection.client.datax_client import DataxClient
from app.module.collection.schema.collection import SyncMode, create_execute_record
from app.module.shared.schema import TaskStatus

logger = get_logger(__name__)

class CollectionTaskService:
    def __init__(self, db: AsyncSession, background_tasks: BackgroundTasks = None):
        self.db = db
        self.background_tasks = background_tasks

    async def create_task(self, task: CollectionTask) -> CollectionTask:
        self.db.add(task)

        # If it's a one-time task, execute it immediately
        if task.sync_mode == SyncMode.ONCE:
            task.status = TaskStatus.RUNNING.name
            asyncio.create_task(self.run_async(task.id))
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
            if not template:
                logger.error(f"template {task.template_name} not exist")
                return
            task_execution = create_execute_record(task)
            session.add(task_execution)
            await session.commit()
            DataxClient(execution=task_execution, task=task).run_datax_job()
            await session.commit()
