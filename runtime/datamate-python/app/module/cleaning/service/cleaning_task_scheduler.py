from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.module.cleaning.repository import CleaningTaskRepository
from app.module.cleaning.runtime_client import RuntimeClient

logger = get_logger(__name__)


class CleaningTaskScheduler:
    """Scheduler for executing cleaning tasks"""

    def __init__(self, task_repo: CleaningTaskRepository, runtime_client: RuntimeClient):
        self.task_repo = task_repo
        self.runtime_client = runtime_client

    async def execute_task(self, db: AsyncSession, task_id: str, retry_count: int) -> bool:
        """Execute cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus
        from datetime import datetime

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.RUNNING
        task.started_at = datetime.now()
        task.retry_count = retry_count

        await self.task_repo.update_task(db, task)
        return await self.runtime_client.submit_task(task_id)

    async def stop_task(self, db: AsyncSession, task_id: str) -> bool:
        """Stop cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus

        await self.runtime_client.stop_task(task_id)

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.STOPPED

        await self.task_repo.update_task(db, task)
        return True
