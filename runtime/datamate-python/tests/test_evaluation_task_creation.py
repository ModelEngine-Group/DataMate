import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exception import BusinessError, ErrorCodes
from app.db.session import get_db
from app.module.evaluation.interface import evaluation as routes
from app.module.evaluation.schema.evaluation import CreateEvaluationTaskRequest
from app.module.evaluation.service import evaluation as service


def _payload(method="MANUAL", **config):
    return {
        "name": "manual evaluation",
        "taskType": "QA",
        "sourceType": "DATASET",
        "sourceId": "dataset-1",
        "sourceName": "dataset",
        "evalMethod": method,
        "evalConfig": {"dimensions": [], **config},
    }


@pytest.mark.parametrize("method", ["MANUAL", "AUTO"])
def test_create_task_preserves_method_and_only_looks_up_models_for_auto(monkeypatch, method):
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        add=Mock(), commit=AsyncMock(), refresh=AsyncMock(),
    )
    lookup = AsyncMock(return_value=SimpleNamespace(model_name="test-model"))
    monkeypatch.setattr(routes, "get_model_by_id", lookup)
    scheduled = []

    def schedule(coroutine):
        scheduled.append(coroutine)
        coroutine.close()

    monkeypatch.setattr(routes, "asyncio", SimpleNamespace(create_task=schedule))
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_db] = lambda: db
    payload = _payload(method, **({"modelId": "model-1"} if method == "AUTO" else {}))

    with TestClient(app) as client:
        response = client.post("/tasks", json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["data"]["evalMethod"] == method
    task = db.add.call_args.args[0]
    assert task.eval_method == method
    assert json.loads(task.eval_config)["modelId"] == ("model-1" if method == "AUTO" else None)
    assert task.status == "PENDING"
    db.commit.assert_awaited_once()
    assert len(scheduled) == 1
    if method == "AUTO":
        lookup.assert_awaited_once_with(db, "model-1")
    else:
        lookup.assert_not_awaited()


@pytest.mark.parametrize("model_id", [None, "", "  "])
def test_auto_task_requires_model_before_database_access(model_id):
    app = FastAPI()
    app.include_router(routes.router)
    db = SimpleNamespace(execute=AsyncMock())
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        response = client.post("/tasks", json=_payload("AUTO", modelId=model_id))
    assert response.status_code == 422
    db.execute.assert_not_awaited()


def test_auto_task_rejects_unknown_model(monkeypatch):
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: None)),
        add=Mock(), commit=AsyncMock(),
    )
    monkeypatch.setattr(routes, "get_model_by_id", AsyncMock(return_value=None))
    request = CreateEvaluationTaskRequest.model_validate(_payload("AUTO", modelId="unknown"))
    with pytest.raises(BusinessError) as error:
        asyncio.run(routes.create_evaluation_task(request, db))
    assert error.value.code == ErrorCodes.EVALUATION_MODEL_NOT_FOUND.code
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.parametrize("method", ["MANUAL", "AUTO"])
@pytest.mark.parametrize("preparation_fails", [False, True])
def test_worker_prepares_manual_items_without_running_the_model(monkeypatch, method, preparation_fails):
    task = SimpleNamespace(id="task-1", source_type="DATASET", eval_method=method, status="PENDING")
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: task)),
        commit=AsyncMock(),
    )

    class Session:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *args):
            return False

    sessions = Mock(side_effect=Session)
    executor = SimpleNamespace(save_eval_items=AsyncMock(), execute=AsyncMock())
    if preparation_fails:
        executor.save_eval_items.side_effect = RuntimeError("invalid dataset")
    monkeypatch.setattr(service, "AsyncSessionLocal", sessions)
    monkeypatch.setattr(service, "EvaluationExecutorFactory", lambda *_: SimpleNamespace(get_executor=lambda _: executor))

    asyncio.run(service.EvaluationTaskService.run_evaluation_task(task.id))

    executor.save_eval_items.assert_awaited_once()
    if preparation_fails:
        assert task.status == "FAILED"
        executor.execute.assert_not_awaited()
        assert sessions.call_count == 1
    elif method == "MANUAL":
        assert task.status == "RUNNING"
        assert task.eval_process == 0
        executor.execute.assert_not_awaited()
        assert sessions.call_count == 1
    else:
        assert task.status == "COMPLETED"
        executor.execute.assert_awaited_once()
        assert sessions.call_count == 2
