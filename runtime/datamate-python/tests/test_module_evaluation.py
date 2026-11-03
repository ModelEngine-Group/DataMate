import asyncio
import json
from types import SimpleNamespace

import pytest

from app.core.exception import BusinessError, ErrorCodes
from app.db.models import EvaluationItem, EvaluationTask
from app.db.models.data_evaluation import EvaluationFile
from app.module.evaluation.schema.prompt import EVALUATION_PROMPT_TEMPLATE
from app.module.evaluation.service import evaluation as evaluation_module
from app.module.evaluation.service.evaluation import (
    DatasetEvaluationExecutor,
    EvaluationExecutor,
)
from app.module.evaluation.service.prompt_template_service import PromptTemplateService
from app.module.shared.schema import TaskStatus


def test_get_prompt_templates_size_matches_source() -> None:
    response = PromptTemplateService.get_prompt_templates()
    assert len(response.templates) == len(EVALUATION_PROMPT_TEMPLATE)


def test_get_prompt_templates_dimensions_are_mapped() -> None:
    response = PromptTemplateService.get_prompt_templates()
    assert response.templates

    first = response.templates[0]
    assert isinstance(first.evalType, str)
    assert isinstance(first.prompt, str)
    for dim in first.defaultDimensions:
        assert isinstance(dim.dimension, str)
        assert isinstance(dim.description, str)


def test_get_prompt_templates_all_items_have_eval_type_and_prompt() -> None:
    response = PromptTemplateService.get_prompt_templates()

    assert all(item.evalType for item in response.templates)
    assert all(isinstance(item.prompt, str) for item in response.templates)


def test_get_prompt_templates_preserves_eval_type_order() -> None:
    response = PromptTemplateService.get_prompt_templates()
    expected = [item.get("evalType", "") for item in EVALUATION_PROMPT_TEMPLATE]
    actual = [item.evalType for item in response.templates]
    assert actual == expected


def test_get_prompt_templates_handles_empty_dimensions() -> None:
    response = PromptTemplateService.get_prompt_templates()
    for idx, raw in enumerate(EVALUATION_PROMPT_TEMPLATE):
        if not raw.get("defaultDimensions"):
            assert response.templates[idx].defaultDimensions == []


def test_prompt_template_dimension_fields_are_non_none() -> None:
    response = PromptTemplateService.get_prompt_templates()
    for item in response.templates:
        for dim in item.defaultDimensions:
            assert dim.dimension is not None
            assert dim.description is not None


class _EmptyResult:
    def scalars(self):
        return self

    def all(self):
        return []

    def scalar_one(self):
        return 0


class _EmptySession:
    async def execute(self, _statement):
        return _EmptyResult()


def _build_task(task_type: str) -> EvaluationTask:
    return EvaluationTask(
        id="task-1",
        name="evaluation-task",
        task_type=task_type,
        source_type="DATASET",
        source_id="dataset-1",
        source_name="dataset",
        eval_config=json.dumps({"modelId": "model-1", "dimensions": []}),
        status="PENDING",
        eval_process=0.0,
    )


def test_execute_raises_business_error_when_task_has_no_items(monkeypatch) -> None:
    async def fake_get_model_by_id(_db, _model_id):
        return object()

    monkeypatch.setattr(evaluation_module, "get_model_by_id", fake_get_model_by_id)
    executor = DatasetEvaluationExecutor(_EmptySession(), _build_task("COT"))

    with pytest.raises(BusinessError) as exc_info:
        asyncio.run(executor.execute())

    assert exc_info.value.code == ErrorCodes.EVALUATION_NO_ITEMS.code


def test_cot_eval_prompt_tolerates_missing_chain_of_thought() -> None:
    executor = EvaluationExecutor(None, _build_task("COT"))
    item = EvaluationItem(
        id="item-1",
        task_id="task-1",
        file_id="file-1",
        item_id="1",
        eval_content=json.dumps({"instruction": "1+1=?", "output": "2"}),
    )

    prompt = executor.get_eval_prompt(item)

    assert "1+1=?" in prompt
    assert "## 思维链:\n\n" in prompt


def test_qa_eval_prompt_tolerates_missing_input_field() -> None:
    executor = EvaluationExecutor(None, _build_task("QA"))
    item = EvaluationItem(
        id="item-1",
        task_id="task-1",
        file_id="file-1",
        item_id="1",
        eval_content=json.dumps({"instruction": "什么是向量检索？", "output": "按相似度检索向量。"}),
    )

    prompt = executor.get_eval_prompt(item)

    assert "{content}" not in prompt
    assert "{question}" not in prompt
    assert "什么是向量检索？" in prompt
    assert "按相似度检索向量。" in prompt


def test_qa_eval_prompt_handles_non_object_eval_content() -> None:
    executor = EvaluationExecutor(None, _build_task("QA"))
    item = EvaluationItem(
        id="item-1",
        task_id="task-1",
        file_id="file-1",
        item_id="1",
        eval_content=json.dumps(["a", "b"]),
    )

    prompt = executor.get_eval_prompt(item)

    assert '["a", "b"]' in prompt


class _CountingSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


def test_evaluate_item_defers_commit_to_the_executor(monkeypatch) -> None:
    monkeypatch.setattr(
        evaluation_module,
        "call_openai_style_model",
        lambda *args, **kwargs: '{"result": {"问题是否独立": "Y"}, "evaluation": "ok"}',
    )
    session = _CountingSession()
    executor = EvaluationExecutor(session, _build_task("QA"))
    item = EvaluationItem(
        id="item-1",
        task_id="task-1",
        file_id="file-1",
        item_id="1",
        eval_content=json.dumps({"instruction": "什么是向量检索？", "output": "按相似度检索向量。"}),
        eval_result="{}",
        status=TaskStatus.PENDING.value,
    )
    models = SimpleNamespace(base_url="http://example.test/v1", api_key="k", model_name="m")

    asyncio.run(executor.evaluate_item(models, item, asyncio.Semaphore(1)))

    assert item.status == TaskStatus.COMPLETED.value
    assert json.loads(item.eval_result)["result"]["问题是否独立"] == "Y"
    assert session.commits == 0


def test_evaluate_item_marks_item_failed_when_model_keeps_failing(monkeypatch) -> None:
    def broken_model(*args, **kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(evaluation_module, "call_openai_style_model", broken_model)
    executor = EvaluationExecutor(_CountingSession(), _build_task("QA"))
    item = EvaluationItem(
        id="item-1",
        task_id="task-1",
        file_id="file-1",
        item_id="1",
        eval_content=json.dumps({"instruction": "q", "output": "a"}),
        eval_result="{}",
        status=TaskStatus.PENDING.value,
    )
    models = SimpleNamespace(base_url="http://example.test/v1", api_key="k", model_name="m")

    asyncio.run(executor.evaluate_item(models, item, asyncio.Semaphore(1)))

    assert item.status == TaskStatus.FAILED.value
    assert item.eval_result == "{}"


class _ScriptedResult:
    def __init__(self, rows=(), scalar=None) -> None:
        self._rows = list(rows)
        self._scalar = scalar

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._scalar


class _ScriptedSession:
    def __init__(self, results) -> None:
        self._results = list(results)
        self.commits = 0

    async def execute(self, _statement):
        return self._results.pop(0)

    async def commit(self) -> None:
        self.commits += 1


def test_execute_reports_failure_when_every_item_fails(monkeypatch) -> None:
    async def fake_get_model_by_id(_db, _model_id):
        return SimpleNamespace(base_url="http://example.test/v1", api_key="k", model_name="m")

    async def fake_evaluate_item(self, _models, item, _semaphore):
        item.status = TaskStatus.FAILED.value

    monkeypatch.setattr(evaluation_module, "get_model_by_id", fake_get_model_by_id)
    monkeypatch.setattr(EvaluationExecutor, "evaluate_item", fake_evaluate_item)

    task = _build_task("QA")
    eval_file = EvaluationFile(
        id="file-row-1",
        task_id=task.id,
        file_id="file-1",
        file_name="qa.jsonl",
        total_count=2,
        evaluated_count=2,
    )
    items = [
        EvaluationItem(
            id=f"item-{index}",
            task_id=task.id,
            file_id="file-1",
            item_id=str(index),
            eval_content=json.dumps({"instruction": "q", "output": "a"}),
            eval_result="{}",
            status=TaskStatus.COMPLETED.value,
        )
        for index in range(2)
    ]
    session = _ScriptedSession(
        [
            _ScriptedResult(rows=[eval_file]),
            _ScriptedResult(scalar=2),
            _ScriptedResult(rows=items),
        ]
    )
    executor = EvaluationExecutor(session, task)

    with pytest.raises(BusinessError) as exc_info:
        asyncio.run(executor.execute())

    assert exc_info.value.code == ErrorCodes.EVALUATION_ALL_ITEMS_FAILED.code
    assert eval_file.evaluated_count == 0
    assert task.eval_process == 0
    assert session.commits == 1


class _StubResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _CapturingSession:
    def __init__(self, rows):
        self._rows = rows
        self.added = []

    async def execute(self, _statement):
        return _StubResult(self._rows)

    def add(self, obj):
        self.added.append(obj)


def _write_cot_jsonl(path, rows) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_dataset_executor_parses_cot_files_without_question_field(tmp_path) -> None:
    file_path = tmp_path / "cot.jsonl"
    _write_cot_jsonl(
        file_path,
        [
            {"instruction": "1+1=?", "output": "2", "chain_of_thought": "1 plus 1 equals 2"},
            {"instruction": "2+2=?", "output": "4", "chain_of_thought": "2 plus 2 equals 4"},
        ],
    )
    dataset_file = SimpleNamespace(
        id="file-1",
        file_name="cot.jsonl",
        file_type="JSONL",
        file_path=str(file_path),
    )
    session = _CapturingSession([dataset_file])
    executor = DatasetEvaluationExecutor(session, _build_task("COT"))

    asyncio.run(executor.save_eval_items())

    items = [obj for obj in session.added if isinstance(obj, EvaluationItem)]
    files = [obj for obj in session.added if isinstance(obj, EvaluationFile)]
    assert len(items) == 2
    assert json.loads(items[0].eval_content)["output"] == "2"
    assert len(files) == 1
    assert files[0].total_count == 2


def test_dataset_executor_fails_clearly_when_no_items_can_be_parsed(tmp_path) -> None:
    file_path = tmp_path / "cot.jsonl"
    _write_cot_jsonl(file_path, [{"foo": "bar"}])
    dataset_file = SimpleNamespace(
        id="file-1",
        file_name="cot.jsonl",
        file_type="JSONL",
        file_path=str(file_path),
    )
    session = _CapturingSession([dataset_file])
    executor = DatasetEvaluationExecutor(session, _build_task("COT"))

    with pytest.raises(BusinessError) as exc_info:
        asyncio.run(executor.save_eval_items())

    assert exc_info.value.code == ErrorCodes.EVALUATION_NO_ITEMS.code
    assert session.added == []
