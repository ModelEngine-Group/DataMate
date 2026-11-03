"""Polling behaviour of the cleaning task scheduler.

The control plane must follow the runtime and the data plane instead of
declaring a task FAILED on the first hiccup: a single unreachable poll or a
NOT_FOUND after the runtime sidecar restarts used to mark long running tasks
as failed while the Ray Job kept running and later wrote COMPLETED.
"""

import asyncio
import time
from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models.cleaning import CleaningTask
from app.module.cleaning.repository.cleaning_task_repository import (
    CleaningTaskRepository,
    TERMINAL_TASK_STATUSES,
)
from app.module.cleaning.schema.cleaning import CleaningTaskStatus
from app.module.cleaning.service import cleaning_task_scheduler as scheduler_module
from app.module.cleaning.service.cleaning_task_scheduler import (
    DB_RECHECK_INTERVAL_SECONDS,
    DEFAULT_ORPHAN_TIMEOUT_SECONDS,
    CleaningTaskScheduler,
    _orphan_timeout_seconds,
)

TASK_ID = "task-1"


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def commit(self) -> None:
        self.committed = True


class FakeRepository:
    def __init__(self, statuses: dict[str, str] | None = None, update_result: bool = True):
        self.statuses = dict(statuses or {})
        self.update_result = update_result
        self.finish_calls: list[tuple[str, str]] = []
        self.status_reads = 0

    async def find_status(self, db, task_id: str):
        self.status_reads += 1
        return self.statuses.get(task_id)

    async def finish_if_unfinished(self, db, task_id: str, status: str, finished_at=None) -> bool:
        self.finish_calls.append((task_id, status))
        if not self.update_result:
            return False
        self.statuses[task_id] = status
        return True


class FakeRuntimeClient:
    def __init__(self, responses: list[dict | None]):
        self.responses = list(responses)
        self.calls = 0

    async def get_task_status(self, task_id: str):
        self.calls += 1
        if not self.responses:
            return None
        if len(self.responses) == 1:
            return self.responses[0]
        return self.responses.pop(0)


def _build(responses, statuses=None, update_result=True):
    repo = FakeRepository(statuses, update_result)
    client = FakeRuntimeClient(responses)
    sessions: list[FakeSession] = []

    def factory() -> FakeSession:
        session = FakeSession()
        sessions.append(session)
        return session

    scheduler = CleaningTaskScheduler(repo, client, session_factory=factory)
    scheduler._polling_task_ids.add(TASK_ID)
    return scheduler, repo, client, sessions


def test_not_found_keeps_task_running() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "NOT_FOUND"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == []
    assert TASK_ID in scheduler._polling_task_ids
    assert TASK_ID in scheduler._unresolved_since


def test_unreachable_runtime_keeps_task_running() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [None], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == []
    assert TASK_ID in scheduler._polling_task_ids


def test_unresolved_task_falls_back_to_failed_after_timeout() -> None:
    async def run():
        scheduler, repo, _client, sessions = _build(
            [{"status": "NOT_FOUND"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        scheduler._unresolved_since[TASK_ID] = time.monotonic() - (
            DEFAULT_ORPHAN_TIMEOUT_SECONDS + 1
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo, sessions

    scheduler, repo, sessions = asyncio.run(run())

    assert repo.finish_calls == [(TASK_ID, CleaningTaskStatus.FAILED)]
    assert TASK_ID not in scheduler._polling_task_ids
    assert sessions and sessions[-1].committed is True


def test_not_found_then_data_plane_completes_is_followed() -> None:
    """Reported symptom: NOT_FOUND after a runtime restart, COMPLETED later.

    The control plane must keep the task RUNNING in between and must not write
    FAILED, otherwise the UI flips back to COMPLETED once the data plane writes.
    """

    async def run():
        scheduler, repo, client, _sessions = _build(
            [{"status": "NOT_FOUND"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )

        for _ in range(3):
            # 模拟每 10 秒回读一次数据库
            scheduler._last_db_check_at.pop(TASK_ID, None)
            await scheduler._poll_task(TASK_ID)

        assert repo.finish_calls == []
        assert TASK_ID in scheduler._polling_task_ids

        # 数据面（Ray Job 执行器）直接写入终态
        repo.statuses[TASK_ID] = CleaningTaskStatus.COMPLETED
        scheduler._last_db_check_at.pop(TASK_ID, None)
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo, client

    scheduler, repo, client = asyncio.run(run())

    assert repo.finish_calls == []
    assert client.calls == 3
    assert TASK_ID not in scheduler._polling_task_ids


def test_running_status_clears_unresolved_timer() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "running"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        scheduler._unresolved_since[TASK_ID] = time.monotonic() - 600
        scheduler._last_log_at[TASK_ID] = time.monotonic()
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == []
    assert TASK_ID not in scheduler._unresolved_since
    assert TASK_ID in scheduler._polling_task_ids


def test_terminal_db_status_stops_polling_without_calling_runtime() -> None:
    async def run():
        scheduler, repo, client, _sessions = _build(
            [{"status": "running"}], {TASK_ID: CleaningTaskStatus.COMPLETED}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo, client

    scheduler, repo, client = asyncio.run(run())

    assert client.calls == 0
    assert repo.finish_calls == []
    assert TASK_ID not in scheduler._polling_task_ids


def test_data_plane_partial_success_stops_polling() -> None:
    async def run():
        scheduler, _repo, client, _sessions = _build(
            [{"status": "running"}], {TASK_ID: CleaningTaskStatus.PARTIAL_SUCCESS}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, client

    scheduler, client = asyncio.run(run())

    assert client.calls == 0
    assert TASK_ID not in scheduler._polling_task_ids


def test_deleted_task_stops_polling() -> None:
    async def run():
        scheduler, _repo, client, _sessions = _build([{"status": "running"}], {})
        await scheduler._poll_task(TASK_ID)
        return scheduler, client

    scheduler, client = asyncio.run(run())

    assert client.calls == 0
    assert TASK_ID not in scheduler._polling_task_ids


def test_completed_status_is_written() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "COMPLETED"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == [(TASK_ID, CleaningTaskStatus.COMPLETED)]
    assert TASK_ID not in scheduler._polling_task_ids


def test_failed_status_is_written() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "failed", "error": "boom"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == [(TASK_ID, CleaningTaskStatus.FAILED)]
    assert TASK_ID not in scheduler._polling_task_ids


def test_cancelled_status_maps_to_stopped() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "cancelled"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == [(TASK_ID, CleaningTaskStatus.STOPPED)]


def test_existing_terminal_status_is_not_overwritten() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "failed"}], {TASK_ID: CleaningTaskStatus.RUNNING}, update_result=False
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == [(TASK_ID, CleaningTaskStatus.FAILED)]
    assert TASK_ID not in scheduler._polling_task_ids


def test_unexpected_payload_keeps_task_running() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"code": "runtime.0009", "message": "config missing"}],
            {TASK_ID: CleaningTaskStatus.RUNNING},
        )
        await scheduler._poll_task(TASK_ID)
        return scheduler, repo

    scheduler, repo = asyncio.run(run())

    assert repo.finish_calls == []
    assert TASK_ID in scheduler._polling_task_ids


def test_db_recheck_is_throttled() -> None:
    async def run():
        scheduler, repo, _client, _sessions = _build(
            [{"status": "running"}], {TASK_ID: CleaningTaskStatus.RUNNING}
        )
        await scheduler._poll_task(TASK_ID)
        await scheduler._poll_task(TASK_ID)
        return repo

    repo = asyncio.run(run())

    assert DB_RECHECK_INTERVAL_SECONDS > 0
    assert repo.status_reads == 1


def test_orphan_timeout_defaults(monkeypatch) -> None:
    monkeypatch.delenv("CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS", raising=False)
    assert _orphan_timeout_seconds() == DEFAULT_ORPHAN_TIMEOUT_SECONDS

    monkeypatch.setenv("CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS", "600")
    assert _orphan_timeout_seconds() == 600.0


def test_orphan_timeout_ignores_invalid_values(monkeypatch) -> None:
    monkeypatch.setenv("CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS", "not-a-number")
    assert _orphan_timeout_seconds() == DEFAULT_ORPHAN_TIMEOUT_SECONDS

    monkeypatch.setenv("CLEANING_POLL_ORPHAN_TIMEOUT_SECONDS", "-5")
    assert _orphan_timeout_seconds() == DEFAULT_ORPHAN_TIMEOUT_SECONDS


def test_terminal_statuses_cover_data_plane_results() -> None:
    assert set(TERMINAL_TASK_STATUSES) == {
        CleaningTaskStatus.COMPLETED,
        CleaningTaskStatus.PARTIAL_SUCCESS,
        CleaningTaskStatus.FAILED,
        CleaningTaskStatus.STOPPED,
    }


def test_scheduler_module_exposes_singleton() -> None:
    scheduler_module._scheduler = None
    first = scheduler_module.get_scheduler()
    second = scheduler_module.get_scheduler()

    assert first is second

    scheduler_module._scheduler = None


def test_finish_if_unfinished_keeps_first_terminal_status() -> None:
    """The guarded update must not overwrite a status the executor already wrote."""

    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: CleaningTask.__table__.create(sync_conn))

        factory = async_sessionmaker(engine, expire_on_commit=False)
        repo = CleaningTaskRepository()

        async with factory() as db:
            db.add(
                CleaningTask(
                    id=TASK_ID,
                    name="demo",
                    status=CleaningTaskStatus.RUNNING,
                    src_dataset_id="dataset-1",
                    src_dataset_name="dataset",
                    retry_count=0,
                )
            )
            await db.commit()

            assert await repo.find_status(db, TASK_ID) == CleaningTaskStatus.RUNNING
            assert await repo.find_status(db, "missing") is None

            written = await repo.finish_if_unfinished(
                db, TASK_ID, CleaningTaskStatus.COMPLETED, datetime.now()
            )
            await db.commit()
            assert written is True
            assert await repo.find_status(db, TASK_ID) == CleaningTaskStatus.COMPLETED

            written_again = await repo.finish_if_unfinished(
                db, TASK_ID, CleaningTaskStatus.FAILED, datetime.now()
            )
            await db.commit()
            assert written_again is False
            assert await repo.find_status(db, TASK_ID) == CleaningTaskStatus.COMPLETED

        await engine.dispose()

    asyncio.run(run())
