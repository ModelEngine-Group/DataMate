import pytest

from app.module.generation.schema.generation import SynthesisType
from app.module.generation.service.prompt import (
    ANSWER_GENERATOR_PROMPT,
    COT_GENERATOR_PROMPT,
    QUESTION_GENERATOR_PROMPT,
    get_prompt,
)


def test_get_prompt_dispatches_by_synthesis_type() -> None:
    assert get_prompt(SynthesisType.QA) == ANSWER_GENERATOR_PROMPT
    assert get_prompt(SynthesisType.COT) == COT_GENERATOR_PROMPT
    assert get_prompt(SynthesisType.QUESTION) == QUESTION_GENERATOR_PROMPT


def test_get_prompt_raises_for_unsupported_type() -> None:
    with pytest.raises(ValueError):
        get_prompt("UNKNOWN")


def test_synthesis_type_values_are_stable() -> None:
    assert SynthesisType.QA.value == "QA"
    assert SynthesisType.COT.value == "COT"
    assert SynthesisType.QUESTION.value == "QUESTION"


def test_get_prompt_error_contains_unsupported_type() -> None:
    with pytest.raises(ValueError) as exc:
        get_prompt("X")

    assert "Unsupported synthesis type" in str(exc.value)


@pytest.mark.parametrize(
    "synth_type,required_text",
    [
        (SynthesisType.QA, "output"),
        (SynthesisType.COT, "chain_of_thought"),
        (SynthesisType.QUESTION, "JSON"),
    ],
)
def test_get_prompt_contains_expected_keywords(synth_type: SynthesisType, required_text: str) -> None:
    prompt = get_prompt(synth_type)
    assert required_text in prompt


def test_synthesis_type_enum_values_are_unique() -> None:
    values = [t.value for t in SynthesisType]
    assert len(values) == len(set(values))
