from __future__ import annotations

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.models.data_collection import CollectionTask
from app.db.session import AsyncSessionLocal
from app.module.collection.schema.collection import SyncMode

logger = get_logger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def start_collection_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()
        logger.info("Collection scheduler started")
    return _scheduler


def shutdown_collection_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Collection scheduler stopped")


def _get_scheduler() -> AsyncIOScheduler:
    if _scheduler is None:
        raise RuntimeError("Collection scheduler not initialized")
    return _scheduler


def schedule_collection_task(task_id: str, schedule_expression: str, dataset_id: Optional[str] = None) -> None:
    scheduler = _get_scheduler()
    trigger = CronTrigger.from_crontab(schedule_expression)
    from app.module.collection.service.collection import CollectionTaskService

    scheduler.add_job(
        CollectionTaskService.run_async,
        trigger=trigger,
        args=[task_id, dataset_id],
        id=f"collection:{task_id}",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    logger.info(f"Scheduled collection task {task_id} with cron {schedule_expression}")


def remove_collection_task(task_id: str) -> None:
    if _scheduler is None:
        return
    job_id = f"collection:{task_id}"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)
        logger.info(f"Removed scheduled collection task {task_id}")


def reschedule_collection_task(task_id: str, schedule_expression: str, dataset_id: Optional[str] = None) -> None:
    remove_collection_task(task_id)
    schedule_collection_task(task_id, schedule_expression, dataset_id)


def validate_schedule_expression(schedule_expression: str) -> None:
    CronTrigger.from_crontab(schedule_expression)


async def load_scheduled_collection_tasks() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CollectionTask).where(
                CollectionTask.sync_mode == SyncMode.SCHEDULED.value,
                CollectionTask.schedule_expression.isnot(None),
            )
        )
        tasks = result.scalars().all()

    for task in tasks:
        if not task.schedule_expression:
            continue
        try:
            schedule_collection_task(task.id, task.schedule_expression)
        except Exception as exc:
            logger.error(f"Failed to schedule task {task.id}: {exc}")
