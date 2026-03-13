"""
策略工厂

根据知识库类型（DOCUMENT/GRAPH）创建对应的知识库策略实例。
"""
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_gen import RagType
from app.core.exception import BusinessError, ErrorCodes
from .base import KnowledgeBaseStrategy


class KnowledgeBaseStrategyFactory:
    """知识库策略工厂
    
    使用工厂模式创建知识库策略实例，支持策略缓存以提高性能。
    """
    
    _strategy_cache: Dict[str, type] = {}
    
    @classmethod
    def register_strategy(cls, rag_type: str, strategy_class: type):
        """注册策略类
        
        Args:
            rag_type: 知识库类型（DOCUMENT/GRAPH）
            strategy_class: 策略类
        """
        cls._strategy_cache[rag_type.upper()] = strategy_class
    
    @classmethod
    def create_strategy(
        cls,
        rag_type: str,
        db: AsyncSession
    ) -> KnowledgeBaseStrategy:
        """创建知识库策略实例
        
        Args:
            rag_type: 知识库类型（DOCUMENT/GRAPH）
            db: 数据库异步 session
            
        Returns:
            知识库策略实例
            
        Raises:
            BusinessError: 不支持的知识库类型
        """
        rag_type_upper = rag_type.upper() if isinstance(rag_type, str) else str(rag_type).upper()
        
        if rag_type_upper not in cls._strategy_cache:
            raise BusinessError(
                ErrorCodes.RAG_UNSUPPORTED_TYPE,
                f"不支持的 RAG 类型: {rag_type}"
            )
        
        strategy_class = cls._strategy_cache[rag_type_upper]
        return strategy_class(db)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的知识库类型列表
        
        Returns:
            支持的类型列表
        """
        return list(cls._strategy_cache.keys())
