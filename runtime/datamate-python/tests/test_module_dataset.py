import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.module.dataset.service.service import Service


def _run(coro):
    return asyncio.run(coro)


def test_create_dataset_uses_default_status_when_not_provided() -> None:
    db = MagicMock()
    first_result = MagicMock()
    first_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=first_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    service = Service(db)
    response = _run(service.create_dataset(name="ds1", dataset_type="TEXT", description="desc"))

    assert response.status == "DRAFT"
    assert response.name == "ds1"
    db.commit.assert_called_once()


def test_get_dataset_returns_none_when_execute_fails() -> None:
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db unavailable"))

    service = Service(db)
    response = _run(service.get_dataset("dataset-1"))

    assert response is None


def test_get_file_download_url_returns_file_path() -> None:
    db = MagicMock()
    fake_file = SimpleNamespace(file_path="/dataset/ds1/a.txt")
    result = MagicMock()
    result.scalar_one_or_none.return_value = fake_file
    db.execute = AsyncMock(return_value=result)

    service = Service(db)
    file_path = _run(service.get_file_download_url("ds1", "file1"))

    assert file_path == "/dataset/ds1/a.txt"


def test_create_dataset_raises_for_duplicated_name() -> None:
    db = MagicMock()
    duplicated = SimpleNamespace(id="d1", name="dup")
    result = MagicMock()
    result.scalar_one_or_none.return_value = duplicated
    db.execute = AsyncMock(return_value=result)
    db.rollback = AsyncMock()

    service = Service(db)

    try:
        _run(service.create_dataset(name="dup", dataset_type="TEXT"))
        raised = False
    except Exception as exc:  # noqa: BLE001
        raised = True
        assert "already exists" in str(exc)

    assert raised is True
    db.rollback.assert_called_once()


def test_get_file_download_url_returns_none_when_file_missing() -> None:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    service = Service(db)
    file_path = _run(service.get_file_download_url("ds1", "missing"))

    assert file_path is None


def test_get_dataset_returns_none_when_not_found() -> None:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    service = Service(db)
    response = _run(service.get_dataset("not-exist"))

    assert response is None


def test_get_dataset_files_returns_paged_response() -> None:
    db = MagicMock()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 2
    files_result = MagicMock()
    files_result.scalars.return_value.all.return_value = [
        SimpleNamespace(
            id="f1",
            file_name="a.txt",
            file_type="txt",
            file_path="/dataset/a.txt",
            file_size=12,
            status="ACTIVE",
            upload_time=None,
            last_access_time=None,
            tags=[],
            tags_updated_at=None,
        ),
        SimpleNamespace(
            id="f2",
            file_name="b.txt",
            file_type="txt",
            file_path="/dataset/b.txt",
            file_size=20,
            status="ACTIVE",
            upload_time=None,
            last_access_time=None,
            tags=[],
            tags_updated_at=None,
        ),
    ]
    db.execute = AsyncMock(side_effect=[count_result, files_result])

    service = Service(db)
    response = _run(service.get_dataset_files("ds1", page=0, size=10))

    assert response is not None
    assert response.totalElements == 2
    assert len(response.content) == 2
    assert response.content[0].fileName == "a.txt"


def test_get_dataset_files_returns_none_when_query_fails() -> None:
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("query fail"))
    service = Service(db)

    response = _run(service.get_dataset_files("ds1"))
    assert response is None
