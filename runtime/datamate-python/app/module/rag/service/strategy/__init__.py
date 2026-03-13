"""
策略模式实现

提供知识库检索和处理的策略模式实现。
"""
from app.db.models.knowledge_gen import RagType
from .base import KnowledgeBaseStrategy
from .factory import KnowledgeBaseStrategyFactory
from .vector_strategy import VectorKnowledgeBaseStrategy
from .graph_strategy import GraphKnowledgeBaseStrategy

KnowledgeBaseStrategyFactory.register_strategy(
    RagType.DOCUMENT.value,
    VectorKnowledgeBaseStrategy
)

KnowledgeBaseStrategyFactory.register_strategy(
    RagType.GRAPH.value,
    GraphKnowledgeBaseStrategy
)

__all__ = [
    "KnowledgeBaseStrategy",
    "KnowledgeBaseStrategyFactory",
    "VectorKnowledgeBaseStrategy",
    "GraphKnowledgeBaseStrategy",
]
