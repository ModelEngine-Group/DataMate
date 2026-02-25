"""
文档加载与分片选项

保留必要的配置项，简化使用。
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.module.rag.schema.enums import ProcessType


@dataclass
class SplitOptions:
    """文档分片选项

    Args:
        process_type: 分片策略
        chunk_size: 块大小（字符）
        overlap_size: 块间重叠
        delimiter: 仅 CUSTOM_SEPARATOR_CHUNK 时有效
    """

    process_type: ProcessType = ProcessType.DEFAULT_CHUNK
    chunk_size: int = 500
    overlap_size: int = 50
    delimiter: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于传递给 load_and_split"""
        return {
            "process_type": self.process_type,
            "chunk_size": self.chunk_size,
            "overlap_size": self.overlap_size,
            "delimiter": self.delimiter,
        }


def default_split_options() -> SplitOptions:
    """默认分片选项：递归分块 500/50"""
    return SplitOptions()
