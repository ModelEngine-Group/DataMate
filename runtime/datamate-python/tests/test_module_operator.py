from unittest.mock import MagicMock

import pytest

from app.module.operator.parsers.parser_holder import ParserHolder
from app.module.operator.parsers.zip_parser import ZipParser


def test_get_parser_returns_zip_parser() -> None:
    holder = ParserHolder()
    parser = holder.get_parser("abc.zip")
    assert isinstance(parser, ZipParser)


def test_get_parser_raises_for_unsupported_file() -> None:
    holder = ParserHolder()
    with pytest.raises(ValueError):
        holder.get_parser("abc.txt")


def test_extract_to_delegates_to_target_parser() -> None:
    holder = ParserHolder()
    fake_parser = MagicMock()
    holder._parsers["zip"] = fake_parser

    holder.extract_to("zip", "archive.zip", "target")

    fake_parser.extract_to.assert_called_once_with("archive.zip", "target")


def test_get_parser_supports_uppercase_extension() -> None:
    holder = ParserHolder()
    parser = holder.get_parser("ABC.ZIP")
    assert isinstance(parser, ZipParser)


def test_parse_yaml_from_archive_delegates_to_selected_parser() -> None:
    holder = ParserHolder()
    fake_parser = MagicMock()
    fake_result = object()
    fake_parser.parse_yaml_from_archive.return_value = fake_result
    holder._parsers["zip"] = fake_parser

    result = holder.parse_yaml_from_archive("zip", "a.zip", "metadata.yml")

    assert result is fake_result
    fake_parser.parse_yaml_from_archive.assert_called_once_with("a.zip", "metadata.yml", None, None)


@pytest.mark.parametrize("name", ["a.tar", "a.gz", "a.tgz"])
def test_get_parser_supports_tar_like_extensions(name: str) -> None:
    holder = ParserHolder()
    parser = holder.get_parser(name)
    assert parser is not None


def test_parse_yaml_from_archive_raises_when_type_unsupported() -> None:
    holder = ParserHolder()
    with pytest.raises(ValueError):
        holder.parse_yaml_from_archive("rar", "a.rar", "metadata.yml")


def test_extract_to_raises_when_type_unsupported() -> None:
    holder = ParserHolder()
    with pytest.raises(ValueError):
        holder.extract_to("rar", "a.rar", "tmp")
