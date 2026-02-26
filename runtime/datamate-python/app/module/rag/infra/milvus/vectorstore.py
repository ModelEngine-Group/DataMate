"""
基于 LangChain Milvus 的向量存储封装

使用 langchain-milvus.Milvus + BM25BuiltInFunction 实现密集向量 + 全文检索，
Milvus 2.6.x 自动处理 BM25 稀疏向量，无需手动生成。

同时提供集合管理辅助函数：drop_collection、rename_collection，供知识库删除/重命名使用。
"""
from __future__ import annotations

import logging
from typing import List, Optional

from langchain_core.documents import Document

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
    from pymilvus import MilvusClient, DataType, FunctionType, CollectionSchema, FieldSchema, Function

    from app.core.exception import BusinessError, ErrorCodes

    try:
        conn_args = _connection_args()

        # 创建 Milvus 客户端
        client = MilvusClient(uri=conn_args["uri"], token="")

        # 检查集合是否已存在
        if client.has_collection(collection_name):
            logger.info("集合 %s 已存在，跳过创建", collection_name)
            return

        # 创建字段
        fields = [
            # 1. 主键字段 id
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=36,
                is_primary=True,
                auto_id=False
            ),
            # 2. 文本字段 text（启用 analyzer 用于 BM25）
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                enable_analyzer=True,
                enable_match=True
            ),
            # 3. 元数据字段 metadata
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON
            ),
            # 4. 密集向量字段 vector
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=dimension
            ),
            # 5. 稀疏向量字段 sparse（BM25）
            FieldSchema(
                name="sparse",
                dtype=DataType.SPARSE_FLOAT_VECTOR
            )
        ]

        # 创建 BM25 函数（不使用 params，避免 Milvus 参数错误）
        function = Function(
            name="text_bm25_emb",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse"]
        )

        # 创建 schema
        schema = CollectionSchema(
            fields=fields,
            functions=[function],
            description="Knowledge base collection",
            enable_dynamic_field=True
        )

        # 创建集合（不包含索引）
        # 索引会在首次插入数据时由 Milvus/LangChain 自动创建
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            consistency_level=consistency_level
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

    from app.core.exception import BusinessError, ErrorCodes

    try:
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_model,
            base_url=base_url,
            api_key=api_key,
        )

        test_text = "test"
        # 直接调用同步的 embed_query 方法
        embedding_vector = embedding.embed_query(test_text)
        dimension = len(embedding_vector)

        logger.info("获取模型 %s 的向量维度: %d", embedding_model, dimension)
        return dimension

    except Exception as e:
        logger.error("获取模型维度失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_EMBEDDING_FAILED, f"获取模型维度失败: {str(e)}") from e


def delete_chunks_by_rag_file_ids(collection_name: str, rag_file_ids: List[str]) -> None:
    """按 RAG 文件 ID 列表删除 Milvus 中的分块。用于文件删除时清理向量数据。"""
    import json
    if not rag_file_ids:
        return
    from pymilvus import MilvusClient

    from app.core.exception import BusinessError, ErrorCodes

    try:
        conn_args = _connection_args()
        client = MilvusClient(uri=conn_args["uri"], token="")

        # metadata 为 JSON 字段，按 rag_file_id 过滤
        # 使用 JSON_CONTAINS 的正确语法
        for rid in rag_file_ids:
            json_value = json.dumps({"rag_file_id": rid})
            filter_expr = f'JSON_CONTAINS(metadata, \'{json_value}\')'
            try:
                client.delete(collection_name=collection_name, filter=filter_expr)
            except Exception as del_err:
                logger.warning("删除分块时部分失败 collection=%s rag_file_id=%s: %s", collection_name, rid, del_err)
        logger.info("已按 rag_file_id 删除集合 %s 中的分块: %s", collection_name, rag_file_ids)
    except Exception as e:
        logger.error("按 rag_file_id 删除 Milvus 分块失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除分块失败: {str(e)}") from e


def chunks_to_langchain_documents(
    chunks: list,
    ids: List[str] = None
) -> tuple[list, List[str]]:
    """将 DocumentChunk 转换为 LangChain Document 格式

    Args:
        chunks: DocumentChunk 列表
        ids: 可选的 ID 列表

    Returns:
        (documents, ids): LangChain Document 列表和对应的 ID 列表
    """
    if ids is None:
        ids = [str(i) for i in range(len(chunks))]

    documents = []
    for chunk, chunk_id in zip(chunks, ids):
        doc = Document(page_content=chunk.text, metadata=chunk.metadata)
        documents.append(doc)

    return documents, ids
