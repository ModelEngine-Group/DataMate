import asyncio
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
        self._polling_tasks: dict[str, asyncio.Task] = {}

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
        submitted = await self.runtime_client.submit_task(task_id, retry_count)

        if submitted:
            # Start background polling to sync task status from runtime
            self._start_status_polling(task_id)

        return submitted

    async def stop_task(self, db: AsyncSession, task_id: str) -> bool:
        """Stop cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus

        # Cancel background polling
        if task_id in self._polling_tasks:
            self._polling_tasks[task_id].cancel()
            del self._polling_tasks[task_id]

        await self.runtime_client.stop_task(task_id)

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.STOPPED

        await self.task_repo.update_task(db, task)
        return True

    def _start_status_polling(self, task_id: str):
        """Start background task to poll runtime for task status"""

        async def _poll_loop():
            from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus
            from app.db.session import AsyncSessionLocal
            from datetime import datetime

            logger.info(f"[Polling] Starting status polling for task {task_id}")
            await asyncio.sleep(5)

            terminal_statuses = {"completed", "failed", "cancelled", "stopped"}
            max_polls = 1800  # Max 1 hour (2s interval)
            poll_count = 0

            while poll_count < max_polls:
                try:
                    status_data = await self.runtime_client.get_task_status(task_id)
                    
                    if status_data is None:
                        poll_count += 1
                        await asyncio.sleep(2)
                        continue

                    current_status = (status_data.get("status", "") or "").lower()
                    logger.debug(f"[Polling] Task {task_id} status: {current_status}")

                    if current_status in terminal_statuses:
                        async with AsyncSessionLocal() as db:
                            task = CleaningTaskDto()
                            task.id = task_id
                            if current_status == "completed":
                                task.status = CleaningTaskStatus.COMPLETED
                            else:
                                task.status = CleaningTaskStatus.FAILED
                            task.finished_at = datetime.now()
                            await self.task_repo.update_task(db, task)
                            await db.commit()
                            logger.info(
                                f"[Polling] Task {task_id} finished: {current_status}"
                            )
                        break

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[Polling] Error polling task {task_id}: {e}")

                poll_count += 1
                await asyncio.sleep(2)
            else:
                logger.warning(f"[Polling] Task {task_id} timed out")

            self._polling_tasks.pop(task_id, None)

        task = asyncio.create_task(_poll_loop())
        self._polling_tasks[task_id] = task
