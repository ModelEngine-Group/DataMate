"""
Abstract Parser
抽象解析器基类
"""
import json
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.module.operator.schema import OperatorDto, OperatorReleaseDto
from app.module.operator.constants import CATEGORY_MAP, CATEGORY_OTHER_VENDOR_ID, CATEGORY_CUSTOMIZED_ID
from app.module.operator.exceptions import FieldNotFoundError


class AbstractParser(ABC):
    """算子文件解析器抽象基类"""

    @abstractmethod
    def parse_yaml_from_archive(
        self,
        archive_path: str,
        entry_path: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> OperatorDto:
        """
        从压缩包内读取指定路径的 yaml 文件并解析为 OperatorDto

        Args:
            archive_path: 压缩包路径（zip 或 tar）
            entry_path: 压缩包内部的文件路径，例如 "config/app.yaml"

        Returns:
            解析后的 OperatorDto
        """
        pass

    @abstractmethod
    def extract_to(self, archive_path: str, target_dir: str) -> None:
        """
        将压缩包解压到目标目录（保持相对路径）

        Args:
            archive_path: 压缩包路径
            target_dir: 目标目录
        """
        pass

    def parse_yaml(
        self,
        yaml_content: str,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> OperatorDto:
        """解析 YAML 内容为 OperatorDto"""
        content: Dict[str, Any] = yaml.safe_load(yaml_content)

        operator = OperatorDto(
            id=self._to_string(content.get("raw_id")),
            name=self._to_string(content.get("name")),
            description=self._to_string(content.get("description")),
            version=self._to_string(content.get("version")),
            inputs=self._to_json(content.get("inputs")),
            outputs=self._to_json(content.get("outputs")),
            runtime=self._to_json(content.get("runtime")),
            settings=self._to_json(content.get("settings")),
            metrics=self._to_json(content.get("metrics")),
            file_name=file_name,
            file_size=file_size,
        )

        # Handle changelog
        changelog = content.get("release")
        if isinstance(changelog, list):
            operator_release = OperatorReleaseDto(
                id=operator.id,
                version=operator.version,
                changelog=changelog
            )
        else:
            operator_release = OperatorReleaseDto(
                id=operator.id,
                version=operator.version,
                changelog=[]
            )
        operator.releases = [operator_release]

        # Build categories
        categories = [
            CATEGORY_MAP.get(self._to_lower(content.get("language")), ""),
            CATEGORY_MAP.get(self._to_lower(content.get("modal")), ""),
            CATEGORY_MAP.get(self._to_lower(content.get("vendor")), CATEGORY_OTHER_VENDOR_ID),
            CATEGORY_CUSTOMIZED_ID,
        ]
        operator.categories = categories

        return operator

    def _to_string(self, obj: Any) -> str:
        """转换为字符串"""
        if obj is None:
            raise FieldNotFoundError("field")
        return str(obj)

    def _to_lower(self, obj: Any) -> str:
        """转换为小写字符串"""
        if obj is None:
            raise FieldNotFoundError("field")
        return str(obj).lower()

    def _to_json(self, obj: Any) -> Optional[str]:
        """转换为 JSON 字符串"""
        if obj is None:
            return None
        try:
            return json.dumps(obj).strip('"').strip("'")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize to JSON: {e}")
