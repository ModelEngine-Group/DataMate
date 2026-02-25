"""
基于 LangChain Milvus 的向量存储封装

使用 langchain-milvus.Milvus + BM25BuiltInFunction 实现密集向量 + 全文检索，
Milvus 2.6.x 自动处理 BM25 稀疏向量，无需手动生成。

同时提供集合管理辅助函数：drop_collection、rename_collection，供知识库删除/重命名使用。
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.module.rag.infra.embeddings import EmbeddingFactory

logger = logging.getLogger(__name__)


def _connection_args() -> dict:
    args: dict = {"uri": settings.milvus_uri}
    if getattr(settings, "milvus_token", None):
        args["token"] = settings.milvus_token
    return args


def _ensure_connection() -> None:
    """确保 Milvus 默认连接已建立（供 utility 使用）。"""
    from pymilvus import connections

    conn_args = _connection_args()
    connections.connect(alias="default", uri=conn_args["uri"], token=conn_args.get("token") or "")


def drop_collection(collection_name: str) -> None:
    """删除 Milvus 集合。用于知识库删除等场景。"""
    from pymilvus import utility

    from app.core.exception import BusinessError, ErrorCodes

    try:
        _ensure_connection()
        if utility.has_collection(collection_name, using="default"):
            utility.drop_collection(collection_name, using="default")
            logger.info("成功删除集合: %s", collection_name)
    except Exception as e:
        logger.error("删除集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除集合失败: {str(e)}") from e


def rename_collection(old_name: str, new_name: str) -> None:
    """重命名 Milvus 集合。用于知识库重命名。"""
    from pymilvus import utility

    from app.core.exception import BusinessError, ErrorCodes

    try:
        _ensure_connection()
        if utility.has_collection(old_name, using="default"):
            utility.rename_collection(old_name, new_name, using="default")
            logger.info("成功重命名集合: %s -> %s", old_name, new_name)
    except Exception as e:
        logger.error("重命名集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"重命名集合失败: {str(e)}") from e


def create_java_compatible_collection(
    collection_name: str,
    dimension: int,
    consistency_level: str = "Strong"
) -> None:
    """创建与 Java 服务兼容的 Milvus 集合

    使用 Java 服务相同的字段命名和结构：
    - id (VarChar, 主键)
    - text (VarChar, with analyzer for BM25)
    - metadata (JSON)
    - vector (FloatVector, 密集向量)
    - sparse (SparseFloatVector, BM25 稀疏向量)

    Args:
        collection_name: 集合名称
        dimension: 向量维度
        consistency_level: 一致性级别
    """
    from pymilvus import MilvusClient, DataType, FunctionType

    from app.core.exception import BusinessError, ErrorCodes

    try:
        conn_args = _connection_args()
        token = conn_args.get("token") if conn_args.get("token") else ""
        client = MilvusClient(uri=conn_args["uri"], token=token)

        # 检查集合是否已存在
        if client.has_collection(collection_name):
            logger.info("集合 %s 已存在，跳过创建", collection_name)
            return

        # 定义 schema
        schema = MilvusClient.create_schema()

        # 1. 主键字段 id
        schema.add_field(
            field_name="id",
            datatype=DataType.VARCHAR,
            max_length=36,
            is_primary=True,
            auto_id=False
        )

        # 2. 文本字段 text（启用 analyzer 用于 BM25）
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            enable_match=True
        )

        # 3. 元数据字段 metadata
        schema.add_field(
            field_name="metadata",
            datatype=DataType.JSON
        )

        # 4. 密集向量字段 vector
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=dimension
        )

        # 5. 稀疏向量字段 sparse（BM25）
        schema.add_field(
            field_name="sparse",
            datatype=DataType.SPARSE_FLOAT_VECTOR
        )

        # 创建集合（BM25 将在首次添加文档时自动配置）
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            consistency_level=consistency_level
        )

        # 创建向量索引
        client.create_index(
            collection_name=collection_name,
            field_name="vector",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {
                    "M": 16,
                    "efConstruction": 256
                }
            }
        )

        logger.info("成功创建 Java 兼容的集合: %s (维度: %d)", collection_name, dimension)

    except Exception as e:
        logger.error("创建集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"创建集合失败: {str(e)}") from e


def get_vector_dimension(embedding_model: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> int:
    """获取嵌入模型的向量维度

    Args:
        embedding_model: 模型名称
        base_url: API 基础 URL
        api_key: API 密钥

    Returns:
        向量维度

    Raises:
        BusinessError: 无法获取维度
    """
    from langchain_core.embeddings import Embeddings

    from app.core.exception import BusinessError, ErrorCodes

    try:
        import asyncio
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_model,
            base_url=base_url,
            api_key=api_key,
        )

        test_text = "test"
        embedding_vector = asyncio.run(asyncio.to_thread(embedding.embed_query, test_text))
        dimension = len(embedding_vector)

        logger.info("获取模型 %s 的向量维度: %d", embedding_model, dimension)
        return dimension

    except Exception as e:
        logger.error("获取模型维度失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_EMBEDDING_FAILED, f"获取模型维度失败: {str(e)}") from e


def delete_chunks_by_rag_file_ids(collection_name: str, rag_file_ids: List[str]) -> None:
    """按 RAG 文件 ID 列表删除 Milvus 中的分块。用于文件删除时清理向量数据。"""
    if not rag_file_ids:
        return
    from pymilvus import MilvusClient

    from app.core.exception import BusinessError, ErrorCodes

    try:
        conn_args = _connection_args()
        client = MilvusClient(uri=conn_args["uri"], token=conn_args.get("token") or None)
        # metadata 为 JSON 字段，按 rag_file_id 过滤
        for rid in rag_file_ids:
            filter_expr = f'metadata["rag_file_id"] == "{rid}"'
            try:
                client.delete(collection_name=collection_name, filter=filter_expr)
            except Exception as del_err:
                logger.warning("删除分块时部分失败 collection=%s rag_file_id=%s: %s", collection_name, rid, del_err)
        logger.info("已按 rag_file_id 删除集合 %s 中的分块: %s", collection_name, rag_file_ids)
    except Exception as e:
        logger.error("按 rag_file_id 删除 Milvus 分块失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除分块失败: {str(e)}") from e


def get_milvus_vectorstore(
    collection_name: str,
    embedding: Embeddings,
    *,
    drop_old: bool = False,
    consistency_level: str = "Strong",
) -> Any:
    """创建带全文检索（BM25）的 Milvus 向量存储实例.

    使用 langchain-milvus.Milvus + BM25BuiltInFunction，支持混合检索。

    Args:
        collection_name: 集合名称（通常为知识库名称）
        embedding: LangChain Embeddings 实例
        drop_old: 是否在创建时删除已存在同名集合
        consistency_level: 一致性级别

    Returns:
        Milvus 向量存储实例，支持 add_documents / similarity_search / as_retriever 等
    """
    from langchain_milvus import BM25BuiltInFunction, Milvus

    return Milvus(
        embedding_function=embedding,
        collection_name=collection_name,
        connection_args=_connection_args(),
        builtin_function=BM25BuiltInFunction(),
        vector_field=["dense", "sparse"],
        consistency_level=consistency_level,
        drop_old=drop_old,
    )


def chunks_to_langchain_documents(
    chunks: List[Any],
    *,
    ids: Optional[List[str]] = None,
    id_key: str = "chunk_id",
) -> tuple[List[Document], List[str]]:
    """将领域 DocumentChunk 列表转为 LangChain Document 列表及 id 列表.

    Args:
        chunks: 分块列表，每项有 .text 与 .metadata
        ids: 若提供则作为文档 id，否则从 metadata[id_key] 取或生成
        id_key: metadata 中作为 id 的键名

    Returns:
        (documents, ids)
    """
    from uuid import uuid4

    documents: List[Document] = []
    out_ids: List[str] = []
    for i, ch in enumerate(chunks):
        text = getattr(ch, "text", str(ch))
        meta = getattr(ch, "metadata", {}) or {}
        if ids and i < len(ids):
            doc_id = ids[i]
        else:
            doc_id = meta.get(id_key) or str(uuid4())
        documents.append(Document(page_content=text, metadata=dict(meta)))
        out_ids.append(doc_id)
    return documents, out_ids
