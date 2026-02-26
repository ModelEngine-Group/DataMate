"""
向量存储工厂

使用 LangChain Milvus 创建向量存储实例，支持混合检索（向量 + BM25）。
"""
from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.module.rag.infra.vectorstore.store import (
    create_collection,
    drop_collection,
    get_vector_dimension,
)


class VectorStoreFactory:
    """LangChain Milvus 向量存储工厂"""

    @staticmethod
    def get_connection_args() -> dict:
        """获取 Milvus 连接参数"""
        args: dict = {"uri": settings.milvus_uri}
        if getattr(settings, "milvus_token", None):
            args["token"] = settings.milvus_token
        return args

    @staticmethod
    def create(
        collection_name: str,
        embedding: Embeddings,
        *,
        drop_old: bool = True,
        consistency_level: str = "Strong",
    ) -> Any:
        """创建 Milvus 向量存储实例（支持混合检索）

        Args:
            collection_name: 集合名称（知识库名称）
            embedding: LangChain Embeddings 实例
            drop_old: 是否删除已存在同名集合
            consistency_level: 一致性级别

        Returns:
            langchain_milvus.Milvus 实例
        """
        from langchain_milvus import BM25BuiltInFunction, Milvus

        # 获取向量维度
        dimension = get_vector_dimension(
            embedding_model="",
            embedding_instance=embedding,
        )

        # 删除旧集合（如果存在）
        if drop_old:
            drop_collection(collection_name)

        # 创建集合（5个字段：id、text、metadata、vector、sparse）
        create_collection(
            collection_name=collection_name,
            dimension=dimension,
            consistency_level=consistency_level,
        )

        # 创建 Milvus 实例
        return Milvus(
            embedding_function=embedding,
            collection_name=collection_name,
            connection_args=VectorStoreFactory.get_connection_args(),
            builtin_function=BM25BuiltInFunction(),
            text_field="text",
            vector_field=["vector"],
            drop_old=False,
            consistency_level=consistency_level,
            auto_id=False,
        )
