import asyncio
import os
import time
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.module.cleaning.repository import CleaningTaskRepository
from app.module.cleaning.runtime_client import RuntimeClient

logger = get_logger(__name__)

# 模块级单例：进程内所有请求共享同一个调度器
_scheduler: "CleaningTaskScheduler | None" = None

POLL_INTERVAL_SECONDS = 2
# runtime 报 RUNNING（或返回无法判定的结果）时，多久回读一次数据库。
# 数据面（Ray Job 执行器）会直接把终态写进 t_clean_task，控制面只是跟随者。
DB_RECHECK_INTERVAL_SECONDS = 10
# runtime 长时间给不出任何结论（不可达 / NOT_FOUND）时，控制面兜底标记 FAILED 的超时。
# 必须明显大于“sidecar 重启后仍在跑”的任务最长耗时，否则又会把运行中的任务判成失败。
DEFAULT_ORPHAN_TIMEOUT_SECONDS = 7200
# 同一个未决任务重复告警的最小间隔
UNRESOLVED_LOG_INTERVAL_SECONDS = 60

# runtime 明确给出终态时才写库，避免控制面覆盖数据面已写入的结果
RUNTIME_COMPLETED_STATUSES = {"completed", "succeeded", "success"}
RUNTIME_FAILED_STATUSES = {"failed", "error"}
RUNTIME_STOPPED_STATUSES = {"cancelled", "canceled", "stopped"}
RUNTIME_ACTIVE_STATUSES = {"pending", "running", "submitted", "submitting", "queued"}
RUNTIME_NOT_FOUND_STATUS = "not_found"


def get_scheduler() -> "CleaningTaskScheduler":
    """获取全局调度器单例，不存在则创建"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CleaningTaskScheduler(
            CleaningTaskRepository(None),
            RuntimeClient()
        )
    return _scheduler


def _orphan_timeout_seconds() -> float:
    """runtime 无法给出结论时，控制面兜底失败的等待时间（秒）"""
    raw = os.getenv("CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS")
    if raw is None or not raw.strip():
        return DEFAULT_ORPHAN_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning(
            f"[Polling] Invalid CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS={raw!r}, "
            f"using default {DEFAULT_ORPHAN_TIMEOUT_SECONDS}s"
        )
        return DEFAULT_ORPHAN_TIMEOUT_SECONDS
    if value <= 0:
        logger.warning(
            f"[Polling] CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS must be positive, "
            f"using default {DEFAULT_ORPHAN_TIMEOUT_SECONDS}s"
        )
        return DEFAULT_ORPHAN_TIMEOUT_SECONDS
    return value


class CleaningTaskScheduler:
    """Scheduler for executing cleaning tasks"""

    def __init__(
        self,
        task_repo: CleaningTaskRepository,
        runtime_client: RuntimeClient,
        session_factory: Optional[Callable[[], AsyncSession]] = None,
    ):
        self.task_repo = task_repo
        self.runtime_client = runtime_client
        self._session_factory = session_factory
        self._polling_task_ids: set[str] = set()  # 待轮询的任务 ID 集合
        self._polling_started: bool = False
        # runtime 无法给出结论的起始时刻（monotonic），用于兜底超时
        self._unresolved_since: dict[str, float] = {}
        # 兜底告警 / 数据库回读的节流时间戳
        self._last_log_at: dict[str, float] = {}
        self._last_db_check_at: dict[str, float] = {}

    def _get_session_factory(self) -> Callable[[], AsyncSession]:
        if self._session_factory is not None:
            return self._session_factory

        from app.db.session import AsyncSessionLocal

        return AsyncSessionLocal

    def _forget(self, task_id: str) -> None:
        """任务结束轮询，清理全部内存状态"""
        self._polling_task_ids.discard(task_id)
        self._unresolved_since.pop(task_id, None)
        self._last_log_at.pop(task_id, None)
        self._last_db_check_at.pop(task_id, None)

    async def execute_task(self, db: AsyncSession, task_id: str, retry_count: int) -> bool:
        """Execute cleaning task"""
        from app.module.cleaning.schema import CleaningTaskDto, CleaningTaskStatus

        task = CleaningTaskDto()
        task.id = task_id
        task.status = CleaningTaskStatus.RUNNING
        task.started_at = datetime.now()
        task.retry_count = retry_count

        submitted = await self.runtime_client.submit_task(task_id, retry_count)

        if submitted:
            await self.task_repo.update_task(db, task)
            self._forget(task_id)
            self._polling_task_ids.add(task_id)
            return submitted

        task.status = CleaningTaskStatus.FAILED
        task.finished_at = datetime.now()
        await self.task_repo.update_task(db, task)

        return submitted

    async def stop_task(self, db: AsyncSession, task_id: str) -> bool:
        """Stop cleaning task"""
        from app.module.cleaning.schema import CleaningTaskStatus

        self._forget(task_id)

        await self.runtime_client.stop_task(task_id)

        await self.task_repo.finish_if_unfinished(
            db, task_id, CleaningTaskStatus.STOPPED, datetime.now()
        )
        return True

    async def startup(self):
        """进程启动时调用：恢复未完成任务的轮询 + 启动全局轮询协程"""
        from app.module.cleaning.schema import CleaningTaskStatus

        # 从数据库恢复所有 RUNNING 状态的任务
        try:
            async with self._get_session_factory()() as db:
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
        """全局轮询协程：轮询所有 RUNNING 任务的 runtime 状态"""
        logger.info("[Polling] Global status polling loop started")

        while True:
            for task_id in list(self._polling_task_ids):
                try:
                    await self._poll_task(task_id)
                except Exception as e:
                    # 单次轮询异常（数据库抖动等）不能把任务判成失败，下个周期重试
                    logger.error(f"[Polling] Error polling task {task_id}: {e}")

            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _poll_task(self, task_id: str):
        """轮询单个任务：先看数据库，再问 runtime"""
        from app.module.cleaning.schema import CleaningTaskStatus

        if await self._task_already_finished(task_id):
            return

        status_data = await self.runtime_client.get_task_status(task_id)
        if status_data is None:
            # runtime 不可达（重启中 / 网络抖动）：保持 RUNNING，等它回来
            await self._handle_unresolved(task_id, "runtime unreachable")
            return

        runtime_status = str(status_data.get("status") or "").strip().lower()
        logger.debug(f"[Polling] Task {task_id} status: {runtime_status!r}")

        if runtime_status in RUNTIME_COMPLETED_STATUSES:
            await self._finish_task(task_id, CleaningTaskStatus.COMPLETED, runtime_status)
            self._forget(task_id)
            return

        if runtime_status in RUNTIME_FAILED_STATUSES:
            error = status_data.get("error")
            if error:
                logger.error(f"[Polling] Task {task_id} failed in runtime: {error}")
            await self._finish_task(task_id, CleaningTaskStatus.FAILED, runtime_status)
            self._forget(task_id)
            return

        if runtime_status in RUNTIME_STOPPED_STATUSES:
            await self._finish_task(task_id, CleaningTaskStatus.STOPPED, runtime_status)
            self._forget(task_id)
            return

        if runtime_status in RUNTIME_ACTIVE_STATUSES:
            # runtime 说还在跑：清掉未决计时，继续等数据面写终态
            self._unresolved_since.pop(task_id, None)
            self._last_log_at.pop(task_id, None)
            return

        if runtime_status == RUNTIME_NOT_FOUND_STATUS:
            # sidecar 重启后内存任务表为空，但 Ray Job 仍在跑并会自己写终态
            await self._handle_unresolved(task_id, "runtime reports NOT_FOUND")
            return

        # 空响应 / 非预期内容（例如配置文件缺失导致的错误体），同样按未决处理
        await self._handle_unresolved(task_id, f"unexpected runtime status {runtime_status!r}")

    async def _task_already_finished(self, task_id: str) -> bool:
        """数据面可能已经直接写了终态，此时不再轮询"""
        from app.module.cleaning.schema import CleaningTaskStatus

        now = time.monotonic()
        if now - self._last_db_check_at.get(task_id, 0.0) < DB_RECHECK_INTERVAL_SECONDS:
            return False
        self._last_db_check_at[task_id] = now

        db_status = await self._read_db_status(task_id)
        if db_status is None:
            logger.info(f"[Polling] Task {task_id} no longer exists, stop polling")
            self._forget(task_id)
            return True

        if db_status in {
            CleaningTaskStatus.COMPLETED,
            CleaningTaskStatus.PARTIAL_SUCCESS,
            CleaningTaskStatus.FAILED,
            CleaningTaskStatus.STOPPED,
        }:
            logger.info(f"[Polling] Task {task_id} already finished in DB: {db_status}")
            self._forget(task_id)
            return True

        return False

    async def _read_db_status(self, task_id: str) -> Optional[str]:
        async with self._get_session_factory()() as db:
            return await self.task_repo.find_status(db, task_id)

    async def _handle_unresolved(self, task_id: str, reason: str):
        """runtime 给不出结论：保持 RUNNING，超时后才兜底置 FAILED"""
        from app.module.cleaning.schema import CleaningTaskStatus

        now = time.monotonic()
        since = self._unresolved_since.setdefault(task_id, now)
        elapsed = now - since
        timeout = _orphan_timeout_seconds()

        if elapsed >= timeout:
            logger.error(
                f"[Polling] Task {task_id} marked FAILED: unresolved for {int(elapsed)}s "
                f"({reason}, timeout={int(timeout)}s)"
            )
            await self._finish_task(task_id, CleaningTaskStatus.FAILED, reason)
            self._forget(task_id)
            return

        if now - self._last_log_at.get(task_id, 0.0) >= UNRESOLVED_LOG_INTERVAL_SECONDS:
            self._last_log_at[task_id] = now
            logger.warning(
                f"[Polling] Task {task_id} still unresolved after {int(elapsed)}s ({reason}); "
                f"keeping status unchanged, will fall back to FAILED after {int(timeout)}s"
            )

    async def _finish_task(self, task_id: str, status: str, reason: str = "") -> None:
        """写入终态；已有终态时不做覆盖（幂等）"""
        async with self._get_session_factory()() as db:
            updated = await self.task_repo.finish_if_unfinished(
                db, task_id, status, datetime.now()
            )
            await db.commit()

        if updated:
            logger.info(f"[Polling] Task {task_id} finished: {status} ({reason})")
        else:
            logger.info(
                f"[Polling] Task {task_id} already has a terminal status, skip writing {status}"
            )
