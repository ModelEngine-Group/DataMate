"""
向量存储模块

提供 Milvus 向量存储的创建、管理和数据操作功能。
"""
from app.module.rag.infra.vectorstore.factory import VectorStoreFactory
from app.module.rag.infra.vectorstore.milvus_client import get_milvus_client
from app.module.rag.infra.vectorstore.store import (
    chunks_to_documents,
    create_collection,
    delete_chunks_by_rag_file_ids,
    drop_collection,
    get_vector_dimension,
    rename_collection,
    update_chunk_by_id,
    delete_chunk_by_id,
)

__all__ = [
    "VectorStoreFactory",
    "get_milvus_client",
    "create_collection",
    "drop_collection",
    "rename_collection",
    "get_vector_dimension",
    "delete_chunks_by_rag_file_ids",
    "chunks_to_documents",
    "update_chunk_by_id",
    "delete_chunk_by_id",
]
