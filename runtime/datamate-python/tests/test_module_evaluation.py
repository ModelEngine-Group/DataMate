from app.module.evaluation.schema.prompt import EVALUATION_PROMPT_TEMPLATE
from app.module.evaluation.service.prompt_template_service import PromptTemplateService


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
