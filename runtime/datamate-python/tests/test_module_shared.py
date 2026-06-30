import json

import pytest

from app.module.shared.util.structured_file import (
    COTItemHandler,
    ItemTypes,
    QAItemHandler,
    StructuredFileHandlerFactory,
)


def test_qa_handler_validate_json_accepts_alpaca_item() -> None:
    handler = QAItemHandler()
    assert handler.validate_json({"instruction": "i", "output": "o"}) is True


def test_get_items_from_jsonl_skips_invalid_rows(tmp_path) -> None:
    file_path = tmp_path / "qa.jsonl"
    rows = [
        {"instruction": "i1", "output": "o1"},
        {"instruction": "missing_output"},
        {"instruction": "i2", "output": "o2"},
    ]
    file_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    handler = QAItemHandler()
    items = handler.get_items_from_file(str(file_path))

    assert len(items) == 2
    assert items[0]["output"] == "o1"
    assert items[1]["output"] == "o2"


def test_factory_get_handler_rejects_unknown_item_type() -> None:
    factory = StructuredFileHandlerFactory()
    with pytest.raises(ValueError):
        factory.get_handler("UNKNOWN")


def test_qa_handler_validate_json_rejects_invalid_item() -> None:
    handler = QAItemHandler()
    assert handler.validate_json({"input": "x"}) is False


def test_factory_get_handler_returns_qa_handler() -> None:
    factory = StructuredFileHandlerFactory()
    handler = factory.get_handler(ItemTypes.QA.value)
    assert isinstance(handler, QAItemHandler)


def test_get_items_from_json_file_for_qa(tmp_path) -> None:
    file_path = tmp_path / "qa.json"
    file_path.write_text(
        json.dumps([
            {"instruction": "q1", "output": "a1"},
            {"instruction": "q2", "output": "a2"},
        ], ensure_ascii=False),
        encoding="utf-8",
    )

    handler = QAItemHandler()
    items = handler.get_items_from_file(str(file_path))

    assert len(items) == 2
    assert items[0]["instruction"] == "q1"


def test_cot_handler_validate_json_requires_question_field() -> None:
    handler = COTItemHandler()
    assert handler.validate_json({"instruction": "x", "output": "y"}) is False


def test_factory_get_handler_returns_cot_handler() -> None:
    factory = StructuredFileHandlerFactory()
    handler = factory.get_handler(ItemTypes.COT.value)
    assert isinstance(handler, COTItemHandler)
