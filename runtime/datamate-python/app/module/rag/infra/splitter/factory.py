"""
文档分块器工厂

根据处理类型创建基于 LangChain 的分块器实例，
对应 Java 的 ProcessType 枚举，供 ETL 与 ingest pipeline 复用。
"""
from typing import Optional

from app.module.rag.infra.splitter.base import DocumentSplitter
from app.module.rag.infra.splitter.langchain_impl import LangChainDocumentSplitter
from app.module.rag.schema.enums import ProcessType


class DocumentSplitterFactory:
    """文档分块器工厂

    基于 LangChain RecursiveCharacterTextSplitter / CharacterTextSplitter:
    - PARAGRAPH_CHUNK: 段落分块
    - SENTENCE_CHUNK: 句子分块
    - LENGTH_CHUNK: 字符长度分块
    - DEFAULT_CHUNK: 默认递归分块（推荐）
    - CUSTOM_SEPARATOR_CHUNK: 自定义分隔符分块

    使用示例：
        splitter = DocumentSplitterFactory.create_splitter(
            ProcessType.DEFAULT_CHUNK,
            chunk_size=500,
            overlap_size=50
        )
        chunks = await splitter.split(document_text)
    """

    @classmethod
    def create_splitter(
        cls,
        process_type: ProcessType,
        chunk_size: int = 500,
        overlap_size: int = 50,
        delimiter: Optional[str] = None,
    ) -> DocumentSplitter:
        """根据处理类型创建对应的分块器（LangChain 实现）.

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
