from __future__ import annotations

import shutil
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import NamedTuple

from app.core.config import settings
from app.core.logging import get_logger
from app.module.shared.schedule import Scheduler

logger = get_logger(__name__)


class DiskUsage(NamedTuple):
    total: int
    used: int
    free: int


class LogPvcMonitor:
    """Monitor log PVC usage and delete oldest log-like files when it is full."""

    def __init__(
        self,
        root_path: str | Path,
        threshold: float,
        delete_batch_size: int,
        file_suffixes: str | Iterable[str],
        disk_usage: Callable[[Path], DiskUsage] = shutil.disk_usage,
        unlink_file: Callable[[Path], None] | None = None,
    ) -> None:
        self.root_path = Path(root_path)
        self.threshold = threshold
        self.delete_batch_size = max(1, delete_batch_size)
        self.file_suffixes = self._normalize_suffixes(file_suffixes)
        self._disk_usage = disk_usage
        self._unlink_file = unlink_file or (lambda path: path.unlink())

    def cleanup_if_needed(self) -> int:
        usage_ratio = self._get_usage_ratio()
        if usage_ratio is None:
            return 0
        if usage_ratio < self.threshold:
            logger.debug(
                "Log PVC usage %.2f%% is below threshold %.2f%%",
                usage_ratio * 100,
                self.threshold * 100,
            )
            return 0

        total_deleted = 0
        logger.warning(
            "Log PVC usage %.2f%% reached threshold %.2f%%, starting cleanup under %s",
            usage_ratio * 100,
            self.threshold * 100,
            self.root_path,
        )

        while usage_ratio >= self.threshold:
            candidates = self._find_candidates()
            if not candidates:
                logger.warning(
                    "Log PVC usage remains %.2f%%, but no matching log files are available under %s",
                    usage_ratio * 100,
                    self.root_path,
                )
                break

            deleted_in_batch = self._delete_batch(candidates[: self.delete_batch_size])
            total_deleted += deleted_in_batch
            if deleted_in_batch == 0:
                logger.warning("Log PVC cleanup made no progress; stopping this cleanup run")
                break

            next_usage_ratio = self._get_usage_ratio()
            if next_usage_ratio is None:
                break
            usage_ratio = next_usage_ratio

        if total_deleted:
            logger.info("Deleted %s files during log PVC cleanup", total_deleted)
        return total_deleted

    def _find_candidates(self) -> list[Path]:
        candidates: list[tuple[float, str, Path]] = []
        if not self.file_suffixes:
            return []

        try:
            paths = self.root_path.rglob("*")
            for path in paths:
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    if path.suffix.lower().lstrip(".") not in self.file_suffixes:
                        continue
                    stat_info = path.stat()
                except OSError as exc:
                    logger.warning("Skipping inaccessible log file candidate %s: %s", path, exc)
                    continue
                candidates.append((stat_info.st_mtime, str(path), path))
        except OSError as exc:
            logger.warning("Failed to scan log PVC path %s: %s", self.root_path, exc)
            return []

        candidates.sort(key=lambda item: (item[0], item[1]))
        return [path for _, _, path in candidates]

    def _delete_batch(self, candidates: list[Path]) -> int:
        deleted = 0
        for path in candidates:
            try:
                self._unlink_file(path)
                deleted += 1
                logger.info("Deleted old log file %s", path)
            except FileNotFoundError:
                logger.info("Log file already deleted before cleanup: %s", path)
            except OSError as exc:
                logger.warning("Failed to delete old log file %s: %s", path, exc)
        return deleted

    def _get_usage_ratio(self) -> float | None:
        try:
            usage = self._disk_usage(self.root_path)
        except OSError as exc:
            logger.warning("Failed to inspect log PVC path %s: %s", self.root_path, exc)
            return None

        if usage.total <= 0:
            logger.warning("Log PVC path %s has invalid total size: %s", self.root_path, usage.total)
            return None
        return usage.used / usage.total

    @staticmethod
    def _normalize_suffixes(file_suffixes: str | Iterable[str]) -> set[str]:
        if isinstance(file_suffixes, str):
            raw_suffixes = file_suffixes.split(",")
        else:
            raw_suffixes = file_suffixes
        return {
            suffix.strip().lower().lstrip(".")
            for suffix in raw_suffixes
            if suffix and suffix.strip().lstrip(".")
        }


def schedule_log_pvc_monitor(scheduler: Scheduler) -> None:
    if not settings.log_pvc_monitor_enabled:
        logger.info("Log PVC monitor is disabled")
        return

    monitor = LogPvcMonitor(
        root_path=settings.log_pvc_monitor_path,
        threshold=settings.log_pvc_monitor_threshold,
        delete_batch_size=settings.log_pvc_monitor_delete_batch_size,
        file_suffixes=settings.log_pvc_monitor_file_suffixes,
    )
    interval_seconds = max(1, settings.log_pvc_monitor_interval_seconds)
    scheduler.add_interval_job(
        job_id="system:log-pvc-monitor",
        seconds=interval_seconds,
        func=monitor.cleanup_if_needed,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    logger.info(
        "Scheduled log PVC monitor for %s every %s seconds",
        settings.log_pvc_monitor_path,
        interval_seconds,
    )
