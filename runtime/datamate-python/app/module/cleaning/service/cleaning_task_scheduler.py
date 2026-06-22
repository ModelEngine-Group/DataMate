import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.module.cleaning.repository import CleaningTaskRepository
from app.module.cleaning.runtime_client import RuntimeClient

logger = get_logger(__name__)

# 模块级单例：进程内所有请求共享同一个调度器
_scheduler: "CleaningTaskScheduler | None" = None


def get_scheduler() -> "CleaningTaskScheduler":
    """获取全局调度器单例，不存在则创建"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CleaningTaskScheduler(
            CleaningTaskRepository(None),
            RuntimeClient()
        )
    return _scheduler


class CleaningTaskScheduler:
    """Scheduler for executing cleaning tasks"""

    def __init__(self, task_repo: CleaningTaskRepository, runtime_client: RuntimeClient):
        self.task_repo = task_repo
        self.runtime_client = runtime_client
        self._polling_task_ids: set[str] = set()  # 待轮询的任务 ID 集合
        self._polling_started: bool = False
        self._poll_failure_count: dict[str, int] = {}  # runtime 不可达连续失败计数
        self._MAX_POLL_FAILURES = 1  # 一次超时(60s) → 标记 FAILED

    async def execute_task(self, db: AsyncSession, task_id: str, retry_count: int) -> bool:
        """Execute cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus
        from datetime import datetime

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.RUNNING
        task.started_at = datetime.now()
        task.retry_count = retry_count

        submitted = await self.runtime_client.submit_task(task_id, retry_count)

        if submitted:
            await self.task_repo.update_task(db, task)
            self._polling_task_ids.add(task_id)
            return submitted

        task.status = CleaningTaskStatus.FAILED
        task.finished_at = datetime.now()
        await self.task_repo.update_task(db, task)

        return submitted

    async def stop_task(self, db: AsyncSession, task_id: str) -> bool:
        """Stop cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus

        self._polling_task_ids.discard(task_id)
        self._poll_failure_count.pop(task_id, None)

        await self.runtime_client.stop_task(task_id)

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.STOPPED

        await self.task_repo.update_task(db, task)
        return True

    async def startup(self):
        """进程启动时调用：恢复未完成任务的轮询 + 启动全局轮询协程"""
        from app.module.cleaning.schema import CleaningTaskStatus
        from app.db.session import AsyncSessionLocal

        # 从数据库恢复所有 RUNNING 状态的任务
        try:
            async with AsyncSessionLocal() as db:
                tasks = await self.task_repo.find_tasks(db, status=CleaningTaskStatus.RUNNING)
                for task in tasks:
                    logger.info(f"[Polling] Recovered RUNNING task from DB: {task.id}")
                    self._polling_task_ids.add(task.id)
        except Exception as e:
            logger.error(f"[Polling] Failed to recover tasks from DB: {e}")

        # 启动全局轮询协程
        if not self._polling_started:
            self._polling_started = True
            asyncio.create_task(self._poll_all_tasks())
            logger.info("[Polling] Global polling loop started")

    async def _poll_all_tasks(self):
        """全局轮询协程：每 2 秒轮询所有 RUNNING 任务的 runtime 状态"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus
        from app.db.session import AsyncSessionLocal
        from datetime import datetime

        logger.info("[Polling] Global status polling loop started")
        terminal_statuses = {"completed", "failed", "cancelled", "stopped"}

        while True:
            task_ids = list(self._polling_task_ids)
            if not task_ids:
                # 没有待轮询任务，休眠后继续等
                await asyncio.sleep(2)
                continue

            for task_id in task_ids:
                try:
                    status_data = await self.runtime_client.get_task_status(task_id)
                    if status_data is None:
                        # runtime 不可达，累计失败计数
                        count = self._poll_failure_count.get(task_id, 0) + 1
                        self._poll_failure_count[task_id] = count
                        logger.warning(
                            f"[Polling] Task {task_id} unreachable ({count}/{self._MAX_POLL_FAILURES})"
                        )
                        if count >= self._MAX_POLL_FAILURES:
                            logger.error(
                                f"[Polling] Task {task_id} marked FAILED: "
                                f"runtime unreachable after {count} attempts"
                            )
                            async with AsyncSessionLocal() as db:
                                task_dto = CleaningTaskDto()
                                task_dto.id = task_id
                                task_dto.status = CleaningTaskStatus.FAILED
                                task_dto.finished_at = datetime.now()
                                await self.task_repo.update_task(db, task_dto)
                                await db.commit()
                            self._polling_task_ids.discard(task_id)
                            self._poll_failure_count.pop(task_id, None)
                        continue

                    # runtime 可达，重置失败计数
                    self._poll_failure_count.pop(task_id, None)

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
                        self._polling_task_ids.discard(task_id)
                        self._poll_failure_count.pop(task_id, None)

                except Exception as e:
                    logger.error(f"[Polling] Error polling task {task_id}: {e}")

            await asyncio.sleep(2)
