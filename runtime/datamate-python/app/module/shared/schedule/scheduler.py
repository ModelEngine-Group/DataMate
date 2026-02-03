from __future__ import annotations

from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.logging import get_logger

logger = get_logger(__name__)


class Scheduler:
    def __init__(self, name: str = "scheduler") -> None:
        self._name = name
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
            self._scheduler.start()
            logger.info(f"{self._name} started")
        return self._scheduler

    def shutdown(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info(f"{self._name} stopped")

    def add_cron_job(
        self,
        job_id: str,
        cron_expression: str,
        func: Callable[..., Any],
        args: Optional[list[Any]] = None,
        kwargs: Optional[dict[str, Any]] = None,
        **job_kwargs: Any,
    ) -> None:
        scheduler = self._get_scheduler()
        trigger = CronTrigger.from_crontab(cron_expression)
        scheduler.add_job(
            func,
            trigger=trigger,
            args=args or [],
            kwargs=kwargs or {},
            id=job_id,
            replace_existing=job_kwargs.pop("replace_existing", True),
            max_instances=job_kwargs.pop("max_instances", 1),
            coalesce=job_kwargs.pop("coalesce", True),
            misfire_grace_time=job_kwargs.pop("misfire_grace_time", 60),
            **job_kwargs,
        )

    def remove_job(self, job_id: str) -> None:
        if self._scheduler is None:
            return
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

    def has_job(self, job_id: str) -> bool:
        if self._scheduler is None:
            return False
        return self._scheduler.get_job(job_id) is not None

    def reschedule_job(
        self,
        job_id: str,
        cron_expression: str,
        func: Callable[..., Any],
        args: Optional[list[Any]] = None,
        kwargs: Optional[dict[str, Any]] = None,
        **job_kwargs: Any,
    ) -> None:
        self.remove_job(job_id)
        self.add_cron_job(
            job_id=job_id,
            cron_expression=cron_expression,
            func=func,
            args=args,
            kwargs=kwargs,
            **job_kwargs,
        )

    @staticmethod
    def validate_cron_expression(cron_expression: str) -> None:
        CronTrigger.from_crontab(cron_expression)

    def _get_scheduler(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            raise RuntimeError(f"{self._name} not initialized")
        return self._scheduler
