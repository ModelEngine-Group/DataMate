"""
Tar File Parser
TAR 文件解析器
"""
import tarfile
import os
from typing import Optional

from app.module.operator.parsers.abstract_parser import AbstractParser
from app.module.operator.schema import OperatorDto


class TarParser(AbstractParser):
    """TAR 压缩包解析器"""

    def parse_yaml_from_archive(
        self,
        archive_path: str,
        entry_path: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> OperatorDto:
        """从 TAR 文件中解析 YAML"""
        try:
            with tarfile.open(archive_path, 'r:*') as tar:
                for member in tar.getmembers():
                    if member.name == entry_path or member.name.endswith(f"/{entry_path}"):
                        file = tar.extractfile(member)
                        if file:
                            content = file.read().decode('utf-8')
                            return self.parse_yaml(content, file_name, file_size)
            raise FileNotFoundError(f"File '{entry_path}' not found in archive")
        except (tarfile.TarError, EOFError) as e:
            raise ValueError(f"Failed to parse TAR file: {e}")

    def extract_to(self, archive_path: str, target_dir: str) -> None:
        """解压 TAR 文件到目标目录"""
        try:
            os.makedirs(target_dir, exist_ok=True)
            with tarfile.open(archive_path, 'r:*') as tar:
                # Safety check: prevent path traversal
                for member in tar.getmembers():
                    if os.path.isabs(member.name) or ".." in member.name.split("/"):
                        raise ValueError(f"Unsafe path in archive: {member.name}")
                tar.extractall(target_dir)
        except (tarfile.TarError, EOFError) as e:
            raise ValueError(f"Failed to extract TAR file: {e}")
