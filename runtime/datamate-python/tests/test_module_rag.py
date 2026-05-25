import pytest

from app.module.rag.service.common.text_cleaner import TextCleaner


def test_clean_removes_control_chars_and_empty_lines() -> None:
    raw = "Hello\x00   world\n\n\n\tLine2\n"

    cleaned = TextCleaner.clean(raw)

    assert cleaned == "Hello world\n Line2"


def test_has_printable_content() -> None:
    assert TextCleaner.has_printable_content("   \n\t") is False
    assert TextCleaner.has_printable_content("  数据A ") is True


def test_clean_returns_empty_string_for_none_or_empty() -> None:
    assert TextCleaner.clean(None) == ""
    assert TextCleaner.clean("") == ""


def test_clean_normalizes_multiple_spaces() -> None:
    cleaned = TextCleaner.clean("A   B\t\tC")
    assert cleaned == "A B C"


def test_remove_control_characters_private_method_behavior() -> None:
    cleaned = TextCleaner._remove_control_characters("ab\x01\x02cd")
    assert cleaned == "abcd"


def test_remove_empty_lines_private_method_behavior() -> None:
    text = "line1\n\n  \nline2\n"
    assert TextCleaner._remove_empty_lines(text) == "line1\nline2"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", False),
        ("\n\t ", False),
        ("A", True),
        (" 1 ", True),
    ],
)
def test_has_printable_content_parametrized(text: str, expected: bool) -> None:
    assert TextCleaner.has_printable_content(text) is expected
