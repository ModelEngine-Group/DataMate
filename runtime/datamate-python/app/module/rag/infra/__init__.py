"""
RAG 基础设施层

提供文档处理、向量存储、嵌入模型和后台任务功能。

使用示例:
    from app.module.rag.infra.document import ingest_file_to_chunks
    from app.module.rag.infra.vectorstore import VectorStoreFactory
    from app.module.rag.infra.task import get_global_pool
"""
from app.module.rag.infra.document import (
    SplitOptions,
    default_split_options,
    ingest_file_to_chunks,
    load_and_split,
)

__all__ = [
    "load_and_split",
    "ingest_file_to_chunks",
    "SplitOptions",
    "default_split_options",
]
