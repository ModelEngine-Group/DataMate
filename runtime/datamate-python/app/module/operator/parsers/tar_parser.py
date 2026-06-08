"""
Tar File Parser
TAR 文件解析器
"""
import tarfile
import os
import shutil
from pathlib import Path
from typing import Optional

from app.module.operator.parsers.abstract_parser import AbstractParser
from app.module.operator.schema import OperatorDto


class TarParser(AbstractParser):
    """TAR 压缩包解析器"""

    @staticmethod
    def _flatten_single_package_dir(target_dir: str) -> None:
        target = Path(target_dir)
        required = ("__init__.py", "metadata.yml", "process.py")
        if all((target / name).exists() for name in required):
            return

        children = [item for item in target.iterdir() if item.name != "__MACOSX"]
        if len(children) != 1 or not children[0].is_dir():
            return

        package_dir = children[0]
        if not all((package_dir / name).exists() for name in required):
            return

        for item in package_dir.iterdir():
            shutil.move(str(item), str(target / item.name))
        shutil.rmtree(package_dir, ignore_errors=True)

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
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)
            with tarfile.open(archive_path, 'r:*') as tar:
                # Safety check: prevent path traversal
                for member in tar.getmembers():
                    if os.path.isabs(member.name) or ".." in member.name.split("/"):
                        raise ValueError(f"Unsafe path in archive: {member.name}")
                tar.extractall(target_dir)
            self._flatten_single_package_dir(target_dir)
        except (tarfile.TarError, EOFError) as e:
            raise ValueError(f"Failed to extract TAR file: {e}")
