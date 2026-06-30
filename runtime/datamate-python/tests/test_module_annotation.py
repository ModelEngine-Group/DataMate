from app.module.annotation.utils.config_validator import LabelStudioConfigValidator
import pytest


def test_validate_xml_success_with_object_and_control() -> None:
    xml = """<View>
    <Image name=\"image\" value=\"$image\"/>
    <Choices name=\"label\" toName=\"image\">
        <Choice value=\"Cat\"/>
        <Choice value=\"Dog\"/>
    </Choices>
</View>"""

    valid, error = LabelStudioConfigValidator.validate_xml(xml)

    assert valid is True
    assert error is None


def test_validate_xml_fails_when_no_controls() -> None:
    xml = """<View><Image name=\"image\" value=\"$image\"/></View>"""

    valid, error = LabelStudioConfigValidator.validate_xml(xml)

    assert valid is False
    assert "No annotation controls" in (error or "")


def test_validate_configuration_json_rejects_unknown_object_reference() -> None:
    config = {
        "labels": [
            {
                "fromName": "sentiment",
                "toName": "missing_object",
                "type": "Choices",
                "options": ["positive", "negative"],
            }
        ],
        "objects": [
            {"name": "text", "type": "Text", "value": "$text"}
        ],
    }

    valid, error = LabelStudioConfigValidator.validate_configuration_json(config)

    assert valid is False
    assert "unknown object" in (error or "")


def test_extract_label_values() -> None:
    xml = """<View>
    <Text name=\"text\" value=\"$text\"/>
    <Choices name=\"sentiment\" toName=\"text\">
        <Choice value=\"positive\"/>
        <Choice value=\"negative\"/>
    </Choices>
</View>"""

    labels = LabelStudioConfigValidator.extract_label_values(xml)

    assert labels == {"sentiment": ["positive", "negative"]}


def test_validate_xml_rejects_invalid_root() -> None:
    xml = """<Root><Text name=\"text\" value=\"$text\"/></Root>"""

    valid, error = LabelStudioConfigValidator.validate_xml(xml)

    assert valid is False
    assert "Root element must be <View>" in (error or "")


def test_validate_configuration_json_requires_labels() -> None:
    valid, error = LabelStudioConfigValidator.validate_configuration_json({"objects": []})

    assert valid is False
    assert "Missing 'labels' field" in (error or "")


def test_validate_xml_fails_for_invalid_xml() -> None:
    xml = "<View><Text></View>"
    valid, error = LabelStudioConfigValidator.validate_xml(xml)
    assert valid is False
    assert "XML parse error" in (error or "")


@pytest.mark.parametrize(
    "label,error_text",
    [
        ({"toName": "obj", "type": "Choices", "options": ["A"]}, "fromName"),
        ({"fromName": "lbl", "type": "Choices", "options": ["A"]}, "toName"),
        ({"fromName": "lbl", "toName": "obj", "options": ["A"]}, "type"),
    ],
)
def test_validate_label_definition_required_fields(label, error_text: str) -> None:
    valid, error = LabelStudioConfigValidator._validate_label_definition(label)
    assert valid is False
    assert error_text in (error or "")


def test_validate_label_definition_rejects_unsupported_type() -> None:
    label = {
        "fromName": "x",
        "toName": "obj",
        "type": "NotSupported",
    }
    valid, error = LabelStudioConfigValidator._validate_label_definition(label)
    assert valid is False
    assert "Unsupported control type" in (error or "")


def test_validate_object_definition_rejects_value_without_dollar_prefix() -> None:
    obj = {"name": "txt", "type": "Text", "value": "text"}
    valid, error = LabelStudioConfigValidator._validate_object_definition(obj)
    assert valid is False
    assert "must start with '$'" in (error or "")


def test_extract_label_values_returns_empty_on_invalid_xml() -> None:
    labels = LabelStudioConfigValidator.extract_label_values("<broken")
    assert labels == {}


def test_validate_xml_requires_control_name_and_to_name() -> None:
    xml = """<View>
    <Text name=\"text\" value=\"$text\"/>
    <Choices toName=\"text\"><Choice value=\"A\"/></Choices>
</View>"""
    valid, error = LabelStudioConfigValidator.validate_xml(xml)
    assert valid is False
    assert "Missing 'name' attribute" in (error or "")

