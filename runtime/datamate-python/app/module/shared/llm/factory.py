# app/core/llm/factory.py
"""
LangChain 模型工厂：基于 OpenAI 兼容接口封装 Chat / Embedding 的创建、健康检查与同步调用。
便于模型配置、RAG、生成、评估等模块统一使用，避免分散的 get_chat_client / get_openai_client。
"""
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


class LLMFactory:
    """基于 LangChain 的 Chat / Embedding 工厂，面向 OpenAI 兼容 API。"""

    @staticmethod
    def create_chat(
        model_name: str,
        base_url: str,
        api_key: str | None = None,
    ) -> BaseChatModel:
        """创建对话模型，兼容 OpenAI 及任意 base_url 的 OpenAI 兼容服务。"""
        return ChatOpenAI(
            model=model_name,
            base_url=base_url or None,
            api_key=SecretStr(api_key or ""),
        )

    @staticmethod
    def create_embedding(
        model_name: str,
        base_url: str,
        api_key: str | None = None,
    ) -> Embeddings:
        """创建嵌入模型，兼容 OpenAI 及任意 base_url 的 OpenAI 兼容服务。"""
        return OpenAIEmbeddings(
            model=model_name,
            base_url=base_url or None,
            api_key=SecretStr(api_key or ""),
        )

    @staticmethod
    def check_health(
        model_name: str,
        base_url: str,
        api_key: str | None,
        model_type: Literal["CHAT", "EMBEDDING"] | str,
    ) -> None:
        """对配置做一次最小化调用进行健康检查，失败则抛出。"""
        if model_type == "CHAT":
            model = LLMFactory.create_chat(model_name, base_url, api_key)
            model.invoke("hello")
        else:
            model = LLMFactory.create_embedding(model_name, base_url, api_key)
            model.embed_query("text")

    @staticmethod
    def get_embedding_dimension(
        model_name: str,
        base_url: str,
        api_key: str | None = None,
    ) -> int:
        """创建 Embedding 模型并返回向量维度。"""
        emb = LLMFactory.create_embedding(model_name, base_url, api_key)
        return len(emb.embed_query("text"))

    @staticmethod
    def invoke_sync(chat_model: BaseChatModel, prompt: str) -> str:
        """同步调用对话模型并返回 content，供 run_in_executor 等场景使用。"""
        return chat_model.invoke(prompt).content
