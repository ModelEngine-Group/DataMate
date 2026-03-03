"""
Milvus 客户端单例管理器

确保 MilvusClient 在全局范围内只创建一个实例，避免重复连接。
"""
from __future__ import annotations

import logging
import threading
from typing import Optional

from pymilvus import MilvusClient

from app.core.config import settings

logger = logging.getLogger(__name__)


class MilvusClientManager:
    """Milvus 客户端单例管理器
    
    使用线程安全的单例模式，确保全局只有一个 MilvusClient 实例。
    """
    
    _instance: Optional[MilvusClientManager] = None
    _lock = threading.Lock()
    _client: Optional[MilvusClient] = None
    
    def __new__(cls) -> MilvusClientManager:
        """单例模式：确保只有一个管理器实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def _get_connection_args() -> dict:
        """获取 Milvus 连接参数"""
        args: dict = {"uri": settings.milvus_uri}
        token = getattr(settings, "milvus_token", None)
        if token:
            args["token"] = token
        return args
    
    def get_client(self) -> MilvusClient:
        """获取 Milvus 客户端实例（单例）
        
        Returns:
            MilvusClient 实例
        """
        if self._client is None:
            with self._lock:
                if self._client is None:
                    conn_args = self._get_connection_args()
                    self._client = MilvusClient(
                        uri=conn_args["uri"],
                        token=conn_args.get("token", "")
                    )
                    logger.info("创建 Milvus 客户端单例: uri=%s", conn_args["uri"])
        return self._client
    
    def close(self) -> None:
        """关闭 Milvus 客户端连接"""
        if self._client is not None:
            with self._lock:
                if self._client is not None:
                    try:
                        self._client.close()
                        logger.info("关闭 Milvus 客户端连接")
                    except Exception as e:
                        logger.warning("关闭 Milvus 客户端时出错: %s", e)
                    finally:
                        self._client = None


def get_milvus_client() -> MilvusClient:
    """获取 Milvus 客户端实例（全局单例）
    
    Returns:
        MilvusClient 实例
    """
    return MilvusClientManager().get_client()
