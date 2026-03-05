"""
LangChain Embeddings 封装

直接使用 LangChain 的 embeddings 功能，支持多种提供商：
- OpenAI: langchain-openai
- Ollama: langchain-community
- 其他: 通过 LangChain 生态
"""
from typing import Optional, Any

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings


class EmbeddingFactory:
    """LangChain Embeddings 工厂类"""

    @staticmethod
    def create_embeddings(
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Embeddings:
        """
        创建 LangChain Embeddings 实例

        Args:
            model_name: 模型名称（如 text-embedding-3-small）
            base_url: API 基础 URL
            api_key: API 密钥
            **kwargs: 其他参数

        Returns:
            LangChain Embeddings 实例
        """
        # OpenAI / OpenAI 兼容接口
        if "openai" in model_name.lower() or model_name.startswith("text-embedding"):
            return OpenAIEmbeddings(
                model=model_name,
                base_url=base_url,
                api_key=api_key,
                **kwargs,
            )
        # Ollama
        if base_url and "ollama" in base_url.lower():
            from langchain_community.embeddings.ollama import OllamaEmbeddings

            return OllamaEmbeddings(
                model=model_name,
                base_url=base_url,
                **kwargs,
            )
        # 默认使用 OpenAI 兼容
        return OpenAIEmbeddings(
            model=model_name,
            base_url=base_url,
            api_key=api_key,
            **kwargs,
        )


__all__ = ["EmbeddingFactory", "Embeddings"]
