"""
文档处理模块

提供文档加载、分块和处理管道功能。

使用示例:
    from app.module.rag.infra.document import (
        ingest_file_to_chunks,
        SplitOptions,
        DocumentChunk,
    )

    chunks = await ingest_file_to_chunks(
        "/path/to/doc.pdf",
        chunk_size=500,
        overlap_size=50,
    )
"""
from app.module.rag.infra.document.processor import (
    SplitOptions,
    default_split_options,
    ingest_file_to_chunks,
    load_and_split,
)
from app.module.rag.infra.document.types import (
    DocumentChunk,
    ParsedDocument,
    langchain_documents_to_parsed,
)

__all__ = [
    # 处理管道入口
    "load_and_split",
    "ingest_file_to_chunks",
    # 选项
    "SplitOptions",
    "default_split_options",
    # 类型
    "DocumentChunk",
    "ParsedDocument",
    "langchain_documents_to_parsed",
]
