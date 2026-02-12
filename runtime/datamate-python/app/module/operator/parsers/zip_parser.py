"""
Zip File Parser
ZIP 文件解析器
"""
import zipfile
import os
from typing import Optional

from app.module.operator.parsers.abstract_parser import AbstractParser
from app.module.operator.schema import OperatorDto


class ZipParser(AbstractParser):
    """ZIP 压缩包解析器"""

    def parse_yaml_from_archive(
        self,
        archive_path: str,
        entry_path: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> OperatorDto:
        """从 ZIP 文件中解析 YAML"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                for name in zf.namelist():
                    if name == entry_path or name.endswith(f"/{entry_path}"):
                        with zf.open(name) as file:
                            content = file.read().decode('utf-8')
                            return self.parse_yaml(content, file_name, file_size)
            raise FileNotFoundError(f"File '{entry_path}' not found in archive")
        except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
            raise ValueError(f"Failed to parse ZIP file: {e}")

    def extract_to(self, archive_path: str, target_dir: str) -> None:
        """解压 ZIP 文件到目标目录"""
        try:
            os.makedirs(target_dir, exist_ok=True)
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Safety check: prevent path traversal
                for name in zf.namelist():
                    if os.path.isabs(name) or ".." in name.split("/"):
                        raise ValueError(f"Unsafe path in archive: {name}")
                zf.extractall(target_dir)
        except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
            raise ValueError(f"Failed to extract ZIP file: {e}")
