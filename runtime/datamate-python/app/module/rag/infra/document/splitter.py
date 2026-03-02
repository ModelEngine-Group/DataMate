"""
文档分块器

包含 DocumentSplitter 基类、工厂和 LangChain 实现。
根据 ProcessType 创建对应的分块策略。
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.module.rag.infra.document.types import DocumentChunk
from app.module.rag.schema.enums import ProcessType


# 各 ProcessType 对应的分隔符配置（优先保持较大语义块）
SEPARATORS_BY_PROCESS_TYPE = {
    ProcessType.PARAGRAPH_CHUNK: ["\n\n", "\n", " ", ""],
    ProcessType.SENTENCE_CHUNK: ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " ", ""],
    ProcessType.DEFAULT_CHUNK: ["\n\n", "\n", " ", ""],
    ProcessType.CUSTOM_SEPARATOR_CHUNK: None,
}


class DocumentSplitter(ABC):
    """文档分块器基类

    所有具体的分块器都需要继承此类并实现 split 方法。
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
    async def split(self, text: str, **metadata: Any) -> List[DocumentChunk]:
        """分割文档

        Args:
            text: 文档文本
            **metadata: 额外的元数据

        Returns:
            分块列表
        """
        pass

    def _create_chunk(self, text: str, chunk_index: int, **metadata: Any) -> DocumentChunk:
        """创建文档分块"""
        chunk_metadata = {"chunk_index": chunk_index, **metadata}
        return DocumentChunk(text=text, metadata=chunk_metadata)


class LangChainDocumentSplitter(DocumentSplitter):
    """基于 LangChain 的分块器实现

    根据 ProcessType 选择 RecursiveCharacterTextSplitter 或 CharacterTextSplitter。
    """

    def __init__(
        self,
        process_type: ProcessType,
        chunk_size: int = 500,
        overlap_size: int = 50,
        delimiter: Optional[str] = None,
    ):
        super().__init__(chunk_size=chunk_size, overlap_size=overlap_size)
        self._process_type = process_type
        self._delimiter = delimiter or "\n\n"
        self._splitter = self._create_splitter()

    def _create_splitter(self) -> RecursiveCharacterTextSplitter | CharacterTextSplitter:
        """创建 LangChain 分块器实例"""
        if self._process_type == ProcessType.LENGTH_CHUNK:
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.overlap_size,
                length_function=len,
            )

        separators = SEPARATORS_BY_PROCESS_TYPE.get(self._process_type)
        if self._process_type == ProcessType.CUSTOM_SEPARATOR_CHUNK:
            separators = [self._delimiter, "\n", " ", ""]
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap_size,
            separators=separators,
            length_function=len,
        )

    async def split(self, text: str, **metadata: Any) -> List[DocumentChunk]:
        """分割文档（异步）"""
        if not text or not text.strip():
            return []

        texts = await asyncio.to_thread(self._splitter.split_text, text)
        return [
            DocumentChunk(text=t, metadata={**metadata, "chunk_index": i})
            for i, t in enumerate(texts)
        ]


class DocumentSplitterFactory:
    """文档分块器工厂

    根据处理类型创建对应的分块器实例。
    """

    @classmethod
    def create_splitter(
        cls,
        process_type: ProcessType,
        chunk_size: int = 500,
        overlap_size: int = 50,
        delimiter: Optional[str] = None,
    ) -> DocumentSplitter:
        """创建分块器

        Args:
            process_type: 处理类型
            chunk_size: 分块大小
            overlap_size: 重叠大小
            delimiter: 自定义分隔符（仅用于 CUSTOM_SEPARATOR_CHUNK）

        Returns:
            DocumentSplitter 实例
        """
        return LangChainDocumentSplitter(
            process_type=process_type,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            delimiter=delimiter,
        )
