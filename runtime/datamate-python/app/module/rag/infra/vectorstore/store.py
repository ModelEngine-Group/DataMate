"""
向量存储管理

提供 Milvus 集合的创建、删除、重命名和数据操作功能。
使用 Milvus 2.6+ 的 BM25 内置函数实现混合检索。

字段结构：
- id (VarChar, 主键)
- text (VarChar, with analyzer for BM25)
- metadata (JSON)
- vector (FloatVector, 密集向量)
- sparse (SparseFloatVector, BM25 稀疏向量)
"""
from __future__ import annotations

import logging
from typing import List, Optional

from langchain_core.documents import Document
from pymilvus import DataType, FunctionType, CollectionSchema, FieldSchema, Function

from app.core.exception import BusinessError, ErrorCodes
from app.module.rag.infra.document.types import DocumentChunk
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore.milvus_client import get_milvus_client

logger = logging.getLogger(__name__)

BATCH_DELETE_SIZE = 500


def _delete_chunks_by_rag_file_id_batched(client, collection_name: str, rag_file_id: str) -> int:
    """分批删除指定 rag_file_id 的所有 chunks

    Args:
        client: Milvus 客户端
        collection_name: 集合名称
        rag_file_id: RAG 文件 ID

    Returns:
        删除的总数量
    """
    filter_expr = f'metadata["rag_file_id"] == "{rag_file_id}"'
    total_deleted = 0

    while True:
        try:
            results = client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=["id"],
                limit=BATCH_DELETE_SIZE,
            )
            if not results:
                break

            chunk_ids = [r["id"] for r in results]
            id_filter = ' || '.join([f'id == "{cid}"' for cid in chunk_ids])
            client.delete(collection_name=collection_name, filter=f"({id_filter})")
            total_deleted += len(chunk_ids)

            if len(chunk_ids) < BATCH_DELETE_SIZE:
                break
        except Exception as e:
            logger.warning("分批删除失败: collection=%s rag_file_id=%s error=%s", collection_name, rag_file_id, e)
            break

    return total_deleted


def drop_collection(collection_name: str) -> None:
    """删除 Milvus 集合

    Args:
        collection_name: 集合名称
    """
    try:
        client = get_milvus_client()
        if client.has_collection(collection_name):
            client.drop_collection(collection_name)
            logger.info("成功删除集合: %s", collection_name)
    except Exception as e:
        logger.error("删除集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除集合失败: {str(e)}") from e


def rename_collection(old_name: str, new_name: str) -> None:
    """重命名 Milvus 集合

    Args:
        old_name: 原集合名称
        new_name: 新集合名称
    """
    from pymilvus import utility, connections
    from app.core.config import settings

    try:
        uri = settings.milvus_uri
        token = getattr(settings, "milvus_token", None) or ""
        connections.connect(
            alias="default",
            uri=uri,
            token=token,
        )
        if utility.has_collection(old_name, using="default"):
            utility.rename_collection(old_name, new_name, using="default")
            logger.info("成功重命名集合: %s -> %s", old_name, new_name)
    except Exception as e:
        logger.error("重命名集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"重命名集合失败: {str(e)}") from e


def create_collection(
    collection_name: str,
    dimension: int,
    consistency_level: str = "Strong",
) -> None:
    """创建 Milvus 集合

    使用标准的5字段结构：id、text、metadata、vector、sparse

    Args:
        collection_name: 集合名称
        dimension: 向量维度
        consistency_level: 一致性级别
    """
    try:
        client = get_milvus_client()

        if client.has_collection(collection_name):
            logger.info("集合 %s 已存在，跳过创建", collection_name)
            return

        # 创建字段
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True, auto_id=False),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        ]

        # 创建 BM25 函数
        bm25_function = Function(
            name="text_bm25_emb",
            function_type=FunctionType.BM25,
            input_field_names=["text"],
            output_field_names=["sparse"],
        )

        schema = CollectionSchema(
            fields=fields,
            functions=[bm25_function],
            description="Knowledge base collection",
            enable_dynamic_field=False,
        )

        # BM25 索引参数
        sparse_index_params = {
            "inverted_index_algo": "DAAT_MAXSCORE",
            "bm25_k1": 1.2,
            "bm25_b": 0.75,
        }

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="sparse",
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="BM25",
            params=sparse_index_params
        )
        index_params.add_index(
            field_name="vector",
            index_type="FLAT",
            metric_type="COSINE",
            params={}
        )

        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
            consistency_level=consistency_level,
        )

        logger.info("成功创建集合: %s (维度: %d)", collection_name, dimension)

    except Exception as e:
        logger.error("创建集合失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"创建集合失败: {str(e)}") from e


def get_vector_dimension(
    embedding_model: str = "",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    embedding_instance=None,
) -> int:
    """获取嵌入模型的向量维度

    Args:
        embedding_model: 模型名称
        base_url: API 基础 URL
        api_key: API 密钥
        embedding_instance: 已有的 Embeddings 实例（优先使用）

    Returns:
        向量维度
    """
    try:
        if embedding_instance:
            embedding = embedding_instance
        else:
            embedding = EmbeddingFactory.create_embeddings(
                model_name=embedding_model,
                base_url=base_url,
                api_key=api_key,
            )

        test_vector = embedding.embed_query("test")
        dimension = len(test_vector)
        logger.info("获取向量维度: %d", dimension)
        return dimension

    except Exception as e:
        logger.error("获取向量维度失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_EMBEDDING_FAILED, f"获取向量维度失败: {str(e)}") from e


def delete_chunks_by_rag_file_ids(collection_name: str, rag_file_ids: List[str]) -> None:
    """按 RAG 文件 ID 列表删除 Milvus 中的分块

    Args:
        collection_name: 集合名称
        rag_file_ids: RAG 文件 ID 列表
    """
    if not rag_file_ids:
        return

    try:
        client = get_milvus_client()

        for rid in rag_file_ids:
            deleted = _delete_chunks_by_rag_file_id_batched(client, collection_name, rid)
            logger.info("删除文件分块: collection=%s rag_file_id=%s deleted=%d", collection_name, rid, deleted)

        logger.info("已按 rag_file_id 删除集合 %s 中的分块: %s", collection_name, rag_file_ids)

    except Exception as e:
        logger.error("删除 Milvus 分块失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除分块失败: {str(e)}") from e


def chunks_to_documents(
    chunks: List[DocumentChunk],
    ids: Optional[List[str]] = None,
) -> tuple[List[Document], List[str]]:
    """将 DocumentChunk 转换为 LangChain Document 格式

    Args:
        chunks: DocumentChunk 列表
        ids: 可选的 ID 列表

    Returns:
        (documents, ids): LangChain Document 列表和对应的 ID 列表
    """
    if ids is None:
        import uuid
        ids = [str(uuid.uuid4()) for _ in chunks]

    documents = []
    for chunk, chunk_id in zip(chunks, ids):
        doc = Document(page_content=chunk.text, metadata=chunk.metadata)
        documents.append(doc)

    return documents, ids


def update_chunk_by_id(
    collection_name: str,
    chunk_id: str,
    text: str,
    metadata: Optional[dict] = None,
    embedding_instance=None,
) -> None:
    """更新指定 ID 的分块

    Args:
        collection_name: 集合名称
        chunk_id: 分块 ID
        text: 新的文本内容
        metadata: 新的元数据（可选）
        embedding_instance: Embeddings 实例
    """
    try:
        client = get_milvus_client()

        filter_expr = f'id == "{chunk_id}"'
        existing = client.query(
            collection_name=collection_name,
            filter=filter_expr,
            output_fields=["metadata"],
        )

        if not existing:
            raise BusinessError(
                ErrorCodes.RAG_CHUNK_NOT_FOUND,
                f"Chunk not found: {chunk_id}"
            )

        existing_metadata = existing[0].get("metadata", {})

        if metadata is None:
            metadata = existing_metadata
        else:
            # 确保保留原有的 rag_file_id 字段，防止用户修改时丢失
            if "rag_file_id" in existing_metadata and "rag_file_id" not in metadata:
                metadata = {**metadata, "rag_file_id": existing_metadata["rag_file_id"]}

        if embedding_instance:
            embedding = embedding_instance
        else:
            from app.module.rag.infra.embeddings import EmbeddingFactory
            embedding = EmbeddingFactory.create_embeddings()

        vector = embedding.embed_query(text)

        client.delete(collection_name=collection_name, filter=filter_expr)

        client.insert(
            collection_name=collection_name,
            data=[{
                "id": chunk_id,
                "text": text,
                "metadata": metadata,
                "vector": vector,
            }]
        )

        logger.info("成功更新分块: collection=%s chunk_id=%s", collection_name, chunk_id)

    except BusinessError:
        raise
    except Exception as e:
        logger.error("更新分块失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"更新分块失败: {str(e)}") from e


def delete_chunk_by_id(collection_name: str, chunk_id: str) -> Optional[str]:
    """删除指定 ID 的分块

    Args:
        collection_name: 集合名称
        chunk_id: 分块 ID

    Returns:
        被删除分块对应的 rag_file_id（如果存在），否则返回 None
    """
    try:
        client = get_milvus_client()

        filter_expr = f'id == "{chunk_id}"'

        # 先查询 chunk 的 metadata 获取 rag_file_id
        existing = client.query(
            collection_name=collection_name,
            filter=filter_expr,
            output_fields=["metadata"],
        )

        rag_file_id = None
        if existing:
            metadata = existing[0].get("metadata", {})
            rag_file_id = metadata.get("rag_file_id")

        client.delete(collection_name=collection_name, filter=filter_expr)

        logger.info("成功删除分块: collection=%s chunk_id=%s rag_file_id=%s", collection_name, chunk_id, rag_file_id)

        return rag_file_id

    except Exception as e:
        logger.error("删除分块失败: %s", e)
        raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"删除分块失败: {str(e)}") from e
