"""
基于 LangChain 的文档分片实现

将 ProcessType 映射到 LangChain 的 RecursiveCharacterTextSplitter / CharacterTextSplitter，
在 asyncio.to_thread 中执行同步 split，并转换为领域模型 DocumentChunk。
"""
from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from app.module.rag.schema.enums import ProcessType

from app.module.rag.infra.splitter.base import DocumentChunk, DocumentSplitter


# 各 ProcessType 对应的 RecursiveCharacterTextSplitter 分隔符（优先保持较大语义块）
SEPARATORS_BY_PROCESS_TYPE = {
    ProcessType.PARAGRAPH_CHUNK: ["\n\n", "\n", " ", ""],
    ProcessType.SENTENCE_CHUNK: ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " ", ""],
    ProcessType.DEFAULT_CHUNK: ["\n\n", "\n", " ", ""],  # 推荐默认，递归按段/行/词
    ProcessType.CUSTOM_SEPARATOR_CHUNK: None,  # 由调用方传入 delimiter，动态构造
}


def _build_recursive_splitter(
    chunk_size: int,
    chunk_overlap: int,
    separators: Optional[List[str]] = None,
) -> RecursiveCharacterTextSplitter:
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
    )


def _build_character_splitter(
    chunk_size: int,
    chunk_overlap: int,
) -> CharacterTextSplitter:
    return CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )


def _texts_to_chunks(texts: List[str], **base_metadata: Any) -> List[DocumentChunk]:
    """将切分后的字符串列表转为 DocumentChunk 列表，保留 chunk_index 等."""
    return [
        DocumentChunk(
            text=t,
            metadata={**base_metadata, "chunk_index": i},
        )
        for i, t in enumerate(texts)
    ]


class LangChainDocumentSplitter(DocumentSplitter):
    """基于 LangChain 的 DocumentSplitter 实现.

    根据 ProcessType 选择 RecursiveCharacterTextSplitter 或 CharacterTextSplitter，
    async split() 内部用 asyncio.to_thread 调用同步 split_text，再转为 DocumentChunk。
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
        if self._process_type == ProcessType.LENGTH_CHUNK:
            return _build_character_splitter(
                self.chunk_size,
                self.overlap_size,
            )
        separators = SEPARATORS_BY_PROCESS_TYPE.get(self._process_type)
        if self._process_type == ProcessType.CUSTOM_SEPARATOR_CHUNK:
            separators = [self._delimiter, "\n", " ", ""]
        if separators is None:
            separators = ["\n\n", "\n", " ", ""]
        return _build_recursive_splitter(
            self.chunk_size,
            self.overlap_size,
            separators=separators,
        )

    async def split(self, text: str, **metadata: Any) -> List[DocumentChunk]:
        if not text or not text.strip():
            return []
        texts = await asyncio.to_thread(self._splitter.split_text, text)
        return _texts_to_chunks(texts, **metadata)
