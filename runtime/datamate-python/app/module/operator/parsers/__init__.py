"""
Operator File Parsers
算子文件解析器
"""
from .abstract_parser import AbstractParser
from .tar_parser import TarParser
from .zip_parser import ZipParser
from .parser_holder import ParserHolder

__all__ = [
    "AbstractParser",
    "TarParser",
    "ZipParser",
    "ParserHolder",
]
