"""Exercise the list handler without importing evaluation execution dependencies."""

import ast
import asyncio
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvaluationTask


def _load_list_handler():
    source = Path(__file__).resolve().parents[1] / "app/module/evaluation/interface/evaluation.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    handler = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_evaluation_tasks")
    handler.decorator_list = []
    namespace = {
        "Optional": Optional,
        "Query": Query,
        "Depends": Depends,
        "AsyncSession": AsyncSession,
        "get_db": lambda: None,
        "select": select,
        "func": func,
        "math": math,
        "EvaluationTask": EvaluationTask,
        "SuccessResponse": SimpleNamespace,
        "PagedEvaluationTaskResponse": SimpleNamespace,
        "_map_to_task_detail_response": lambda task: task,
    }
    exec(compile(ast.Module(body=[handler], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["list_evaluation_tasks"]


@pytest.mark.parametrize("method", [None, "AUTO", "MANUAL"])
def test_evaluation_filters_apply_to_count_and_page(method):
    empty_result = SimpleNamespace(
        scalar_one=lambda: 0,
        scalars=lambda: SimpleNamespace(all=lambda: []),
    )
    session = SimpleNamespace(execute=AsyncMock(return_value=empty_result))
    response = asyncio.run(_load_list_handler()(
        page=2,
        size=12,
        name="evaluation",
        status="COMPLETED",
        task_type="QA",
        eval_method=method,
        db=session,
    ))
    assert response.data.content == []
    assert response.data.page == 2
    assert session.execute.await_count == 2
    for call in session.execute.await_args_list:
        statement = call.args[0]
        params = statement.compile().params
        assert params["name_1"] == "%evaluation%"
        assert params["status_1"] == "COMPLETED"
        assert params["task_type_1"] == "QA"
        if method is None:
            assert "eval_method_1" not in params
        else:
            assert params["eval_method_1"] == method
    page_params = session.execute.await_args_list[1].args[0].compile().params
    assert page_params["param_1"] == 12
    assert page_params["param_2"] == 12
