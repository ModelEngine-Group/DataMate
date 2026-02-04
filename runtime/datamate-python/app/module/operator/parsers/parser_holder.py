"""
Parser Holder
解析器持有者，根据文件类型选择合适的解析器
"""
import os
from typing import Dict, Type, Optional

from app.module.operator.parsers.abstract_parser import AbstractParser
from app.module.operator.parsers.tar_parser import TarParser
from app.module.operator.parsers.zip_parser import ZipParser
from app.module.operator.schema import OperatorDto


class ParserHolder:
    """解析器持有者，根据文件类型选择解析器"""

    def __init__(self):
        self._parsers: Dict[str, AbstractParser] = {
            "tar": TarParser(),
            "gz": TarParser(),
            "tgz": TarParser(),
            "zip": ZipParser(),
        }

    def get_parser(self, file_path: str) -> AbstractParser:
        """根据文件扩展名获取解析器"""
        _, ext = os.path.splitext(file_path)
        file_type = ext.lstrip('.').lower()

        if file_type not in self._parsers:
            raise ValueError(f"Unsupported file type: {file_type}")

        return self._parsers[file_type]

    def parse_yaml_from_archive(
        self,
        file_type: str,
        archive_path: str,
        entry_path: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> OperatorDto:
        """从压缩包解析 YAML"""
        if file_type not in self._parsers:
            raise ValueError(f"Unsupported file type: {file_type}")

        return self._parsers[file_type].parse_yaml_from_archive(
            archive_path,
            entry_path,
            file_name,
            file_size
        )

    def extract_to(self, file_type: str, archive_path: str, target_dir: str) -> None:
        """解压文件到目标目录"""
        if file_type not in self._parsers:
            raise ValueError(f"Unsupported file type: {file_type}")

        self._parsers[file_type].extract_to(archive_path, target_dir)
