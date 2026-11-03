"""Guards around re-executing a cleaning task."""

import asyncio

import pytest

from app.core.exception import BusinessError, ErrorCodes
from app.module.cleaning.schema.cleaning import CleaningTaskDto, CleaningTaskStatus
from app.module.cleaning.service.cleaning_task_service import CleaningTaskService

TASK_ID = "11111111-1111-1111-1111-111111111111"


class FakeTaskRepository:
    def __init__(self, status: str) -> None:
        self.status = status

    async def find_task_by_id(self, db, task_id: str):
        return CleaningTaskDto(
            id=task_id,
            name="demo",
            status=self.status,
            src_dataset_id="dataset-1",
            retry_count=0,
        )


class UnexpectedCallRepository:
    async def find_by_instance_id(self, db, task_id: str, status: str):
        raise AssertionError("result repository must not be touched for a running task")


class UnexpectedScheduler:
    async def execute_task(self, db, task_id: str, retry_count: int) -> bool:
        raise AssertionError("scheduler must not resubmit a running task")


def _service(status: str) -> CleaningTaskService:
    return CleaningTaskService(
        task_repo=FakeTaskRepository(status),
        result_repo=UnexpectedCallRepository(),
        operator_instance_repo=None,
        operator_service=None,
        scheduler=UnexpectedScheduler(),
        validator=None,
        dataset_service=None,
        lineage_service=None,
    )


def test_execute_task_rejects_running_task() -> None:
    with pytest.raises(BusinessError) as exc_info:
        asyncio.run(_service(CleaningTaskStatus.RUNNING).execute_task(None, TASK_ID))

    assert exc_info.value.error_code is ErrorCodes.CLEANING_TASK_STATUS_INVALID
    assert "running" in str(exc_info.value.data).lower()


def test_execute_task_rejects_pending_resubmission_of_running_task_only() -> None:
    """A finished task may be re-executed; only RUNNING is blocked."""
    service = _service(CleaningTaskStatus.COMPLETED)

    with pytest.raises(AssertionError):
        # The guard must not fire for COMPLETED: the flow continues into the
        # result repository, which is faked to fail loudly.
        asyncio.run(service.execute_task(None, TASK_ID))
