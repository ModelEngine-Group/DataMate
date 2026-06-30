import pytest

from app.core.exception import BusinessError
from app.module.cleaning.schema.cleaning import OperatorInstanceDto
from app.module.cleaning.service.cleaning_task_validator import CleaningTaskValidator
from app.module.operator.constants import CATEGORY_DATAMATE_ID, CATEGORY_DATA_JUICER_ID


def _op(op_id: str, inputs: str | None, outputs: str | None, categories: list[str] | None = None) -> OperatorInstanceDto:
    return OperatorInstanceDto(id=op_id, inputs=inputs, outputs=outputs, categories=categories)


def test_check_input_and_output_passes_with_multimodal() -> None:
    instances = [
        _op("a", "text", "multimodal"),
        _op("b", "image", "text"),
    ]

    CleaningTaskValidator.check_input_and_output(instances)


def test_check_input_and_output_raises_on_type_mismatch() -> None:
    instances = [
        _op("a", "text", "image"),
        _op("b", "text", "text"),
    ]

    with pytest.raises(BusinessError):
        CleaningTaskValidator.check_input_and_output(instances)


def test_check_and_get_executor_type_raises_when_mixed_categories() -> None:
    instances = [
        _op("a", None, None, [CATEGORY_DATAMATE_ID]),
        _op("b", None, None, [CATEGORY_DATA_JUICER_ID]),
    ]

    with pytest.raises(BusinessError):
        CleaningTaskValidator.check_and_get_executor_type(instances)


def test_check_and_get_executor_type_defaults_to_datamate() -> None:
    instances = [_op("a", None, None, None)]

    executor = CleaningTaskValidator.check_and_get_executor_type(instances)

    assert executor == "datamate"


def test_check_task_id_raises_when_empty() -> None:
    with pytest.raises(BusinessError):
        CleaningTaskValidator.check_task_id("")


def test_check_task_id_accepts_normal_value() -> None:
    CleaningTaskValidator.check_task_id("task-1")


def test_check_input_and_output_returns_for_empty_instances() -> None:
    CleaningTaskValidator.check_input_and_output([])


def test_check_input_and_output_raises_when_current_has_no_outputs() -> None:
    instances = [
        _op("a", "text", None),
        _op("b", "text", "text"),
    ]
    with pytest.raises(BusinessError):
        CleaningTaskValidator.check_input_and_output(instances)


def test_check_input_and_output_raises_when_next_has_no_inputs() -> None:
    instances = [
        _op("a", "text", "text"),
        _op("b", None, "text"),
    ]
    with pytest.raises(BusinessError):
        CleaningTaskValidator.check_input_and_output(instances)


@pytest.mark.parametrize(
    "out_type,in_type",
    [
        ("text", "text"),
        (" image ", "image"),
        ("AUDIO", "audio"),
    ],
)
def test_check_input_and_output_allows_exact_match_with_normalization(out_type: str, in_type: str) -> None:
    instances = [
        _op("a", "x", out_type),
        _op("b", in_type, "y"),
    ]
    CleaningTaskValidator.check_input_and_output(instances)


def test_check_and_get_executor_type_prefers_datajuicer_when_only_datajuicer() -> None:
    instances = [_op("a", None, None, [CATEGORY_DATA_JUICER_ID])]
    assert CleaningTaskValidator.check_and_get_executor_type(instances) == "default"
