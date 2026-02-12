# app/core/llm/__init__.py
"""
LangChain 模型工厂：统一创建 Chat、Embedding 及健康检查，便于各模块复用。
"""
from .factory import LLMFactory

__all__ = ["LLMFactory"]
