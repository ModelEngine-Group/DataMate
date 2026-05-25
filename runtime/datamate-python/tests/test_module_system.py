import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.module.system.service.common_service import get_model_by_id


def _run(coro):
    return asyncio.run(coro)


def test_get_model_by_id_returns_model_when_found() -> None:
    db = MagicMock()
    model = SimpleNamespace(id="m1")
    result = MagicMock()
    result.scalar_one_or_none.return_value = model
    db.execute = AsyncMock(return_value=result)

    fetched = _run(get_model_by_id(db, "m1"))

    assert fetched is model


def test_get_model_by_id_returns_none_when_missing() -> None:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    fetched = _run(get_model_by_id(db, "missing"))

    assert fetched is None


def test_get_model_by_id_invokes_db_execute_once() -> None:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    _run(get_model_by_id(db, "m2"))

    db.execute.assert_called_once()


def test_get_model_by_id_passes_query_object_to_execute() -> None:
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    _run(get_model_by_id(db, "model-xyz"))

    args, _ = db.execute.call_args
    assert len(args) == 1
    assert args[0] is not None


def test_get_model_by_id_returns_exact_scalar_object() -> None:
    db = MagicMock()
    model_obj = SimpleNamespace(id="m100", endpoint="x")
    result = MagicMock()
    result.scalar_one_or_none.return_value = model_obj
    db.execute = AsyncMock(return_value=result)

    fetched = _run(get_model_by_id(db, "m100"))
    assert fetched is model_obj
