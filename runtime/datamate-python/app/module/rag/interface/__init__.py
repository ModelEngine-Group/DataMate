"""
RAG 模块 API 路由导出

集中导出所有 API 路由
"""
from .knowledge_base import router as knowledge_base_router
from .rag_interface import router as graph_rag_router

__all__ = [
    "knowledge_base_router",
    "graph_rag_router",
]
