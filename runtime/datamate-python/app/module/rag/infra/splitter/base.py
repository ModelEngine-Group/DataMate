"""
文档分块器基类

定义文档分块器的抽象接口
使用策略模式支持多种分块策略
"""
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """文档分块

    包含分块的文本和元数据
    """
    text: str
    metadata: dict

    def __repr__(self):
        return f"<DocumentChunk(text_length={len(self.text)}, metadata={self.metadata})>"


class DocumentSplitter(ABC):
    """文档分块器基类（抽象类）

    所有具体的分块器都需要继承此类并实现 split 方法
    """

    def __init__(self, chunk_size: int = 500, overlap_size: int = 50):
        """初始化分块器

        Args:
            chunk_size: 分块大小
            overlap_size: 重叠大小
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

    @abstractmethod
    async def split(self, text: str, **metadata) -> List[DocumentChunk]:
        """分割文档

        Args:
            text: 文档文本
            **metadata: 额外的元数据

        Returns:
            List[DocumentChunk]: 分块列表
        """
        pass

    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        **metadata
    ) -> DocumentChunk:
        """创建文档分块

        Args:
            text: 分块文本
            chunk_index: 分块索引
            **metadata: 额外的元数据

        Returns:
            DocumentChunk: 文档分块
        """
        chunk_metadata = {
            "chunk_index": chunk_index,
            **metadata
        }
        return DocumentChunk(text=text, metadata=chunk_metadata)
