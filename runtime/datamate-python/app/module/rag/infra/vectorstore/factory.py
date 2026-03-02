"""
向量存储工厂

使用 LangChain Milvus 创建向量存储实例，支持混合检索（向量 + BM25）。
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.module.rag.infra.vectorstore.store import (
    create_collection,
    drop_collection,
    get_vector_dimension,
)

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """LangChain Milvus 向量存储工厂
    
    使用单例模式缓存 Milvus 实例，确保每个 collection 只有一个实例。
    """

    _instances: Dict[str, Any] = {}
    _lock = threading.Lock()

    @staticmethod
    def get_connection_args() -> dict:
        """获取 Milvus 连接参数"""
        args: dict = {"uri": settings.milvus_uri}
        if getattr(settings, "milvus_token", None):
            args["token"] = settings.milvus_token
        return args

    @classmethod
    def create(
        cls,
        collection_name: str,
        embedding: Embeddings,
        *,
        drop_old: bool = False,
        consistency_level: str = "Strong",
        force_new: bool = False,
    ) -> Any:
        """创建或获取 Milvus 向量存储实例（支持混合检索）

        Args:
            collection_name: 集合名称（知识库名称）
            embedding: LangChain Embeddings 实例
            drop_old: 是否删除已存在同名集合（默认 False，避免数据丢失）
            consistency_level: 一致性级别
            force_new: 是否强制创建新实例（默认 False，优先使用缓存）

        Returns:
            langchain_milvus.Milvus 实例
        """
        if drop_old:
            drop_collection(collection_name)
            with cls._lock:
                cls._instances.pop(collection_name, None)

        if not force_new and collection_name in cls._instances:
            logger.debug("使用缓存的 Milvus 实例: %s", collection_name)
            return cls._instances[collection_name]

        from langchain_milvus import BM25BuiltInFunction, Milvus

        dimension = get_vector_dimension(
            embedding_model="",
            embedding_instance=embedding,
        )

        create_collection(
            collection_name=collection_name,
            dimension=dimension,
            consistency_level=consistency_level,
        )

        instance = Milvus(
            embedding_function=embedding,
            collection_name=collection_name,
            connection_args=cls.get_connection_args(),
            builtin_function=BM25BuiltInFunction(),
            text_field="text",
            vector_field=["vector"],
            drop_old=False,
            consistency_level=consistency_level,
            auto_id=False,
            primary_field="id",
            metadata_field="metadata",
            enable_dynamic_field=False,
            metadata_schema={"metadata": "JSON"},
        )

        with cls._lock:
            cls._instances[collection_name] = instance
            logger.info("创建并缓存 Milvus 实例: %s", collection_name)

        return instance

    @classmethod
    def clear_cache(cls, collection_name: Optional[str] = None) -> None:
        """清除缓存

        Args:
            collection_name: 集合名称，如果为 None 则清除所有缓存
        """
        with cls._lock:
            if collection_name:
                cls._instances.pop(collection_name, None)
                logger.info("清除 Milvus 实例缓存: %s", collection_name)
            else:
                cls._instances.clear()
                logger.info("清除所有 Milvus 实例缓存")
