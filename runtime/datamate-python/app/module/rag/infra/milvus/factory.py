"""
向量存储工厂

使用 LangChain Milvus 创建向量存储实例，支持混合检索（向量 + BM25）
"""
from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings

from app.core.config import settings


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
        drop_old: bool = False,
        consistency_level: str = "Strong",
    ) -> Any:
        """
        创建 Milvus 向量存储实例（支持混合检索）

        Args:
            collection_name: 集合名称（知识库名称）
            embedding: LangChain Embeddings 实例
            drop_old: 是否删除已存在同名集合
            consistency_level: 一致性级别

        Returns:
            langchain_milvus.Milvus 实例
        """
        from langchain_milvus import BM25BuiltInFunction, Milvus

        return Milvus(
            embedding_function=embedding,
            collection_name=collection_name,
            connection_args=VectorStoreFactory.get_connection_args(),
            builtin_function=BM25BuiltInFunction(),
            vector_field=["dense", "sparse"],
            consistency_level=consistency_level,
            drop_old=drop_old,
        )
