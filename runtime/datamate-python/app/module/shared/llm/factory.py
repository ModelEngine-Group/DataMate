# app/core/llm/factory.py
"""
LangChain 模型工厂：基于 OpenAI 兼容接口封装 Chat / Embedding 的创建、健康检查与同步调用。
便于模型配置、RAG、生成、评估等模块统一使用，避免分散的 get_chat_client / get_openai_client。
"""
import httpx
from typing import Literal

import httpx
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


class LLMFactory:
    """基于 LangChain 的 Chat / Embedding 工厂，面向 OpenAI 兼容 API。"""

    custom_http_client = httpx.Client(verify=False)

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
            http_client=LLMFactory.custom_http_client,
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
    def create_multimodal_embedding(
        model_name: str,
        base_url: str,
        api_key: str | None = None,
    ) -> "MultimodalEmbedding":
        """创建多模态嵌入模型，用于处理图像+文本的嵌入。"""
        return MultimodalEmbedding(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
        )

    @staticmethod
    def check_health(
        model_name: str,
        base_url: str,
        api_key: str | None,
        model_type: Literal["CHAT", "EMBEDDING", "MULTIMODAL_EMBEDDING"] | str,
    ) -> None:
        """对配置做一次最小化调用进行健康检查，失败则抛出。"""
        if model_type == "CHAT":
            model = LLMFactory.create_chat(model_name, base_url, api_key)
            model.invoke("hello")
        elif model_type == "MULTIMODAL_EMBEDDING":
            model = LLMFactory.create_multimodal_embedding(model_name, base_url, api_key)
            model.embed_text("text")
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


class MultimodalEmbedding:
    """多模态嵌入模型客户端，支持文本和图像的嵌入。"""

    def __init__(self, model_name: str, base_url: str, api_key: str | None = None):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.is_dashscope = "dashscope.aliyuncs.com" in base_url
        self.api_endpoint = self._detect_api_endpoint()

    def _detect_api_endpoint(self) -> str:
        """检测 API 提供商并设置对应的端点。"""
        if self.is_dashscope:
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
        return f"{self.base_url}/embeddings"

    def _build_request_body(self, contents: list[dict]) -> dict:
        """构建请求体。"""
        if self.is_dashscope:
            # 阿里云百炼 HTTP API 格式: input.contents
            return {
                "model": self.model_name,
                "input": {"contents": contents},
                "parameters": {},
            }
        # 通用格式: input 数组
        return {
            "model": self.model_name,
            "input": contents,
        }

    def embed_text(self, text: str) -> list[float]:
        """对纯文本进行嵌入。"""
        contents = [{"text": text}]
        return self._embed(contents)

    def embed_image(self, image_url: str, text: str = "") -> list[float]:
        """对图像（可选文本）进行嵌入。"""
        content = {"image": image_url}
        if text:
            content["text"] = text
        contents = [content]
        return self._embed(contents)

    def embed_video(self, video_url: str, text: str = "") -> list[float]:
        """对视频（可选文本）进行嵌入。"""
        content = {"video": video_url}
        if text:
            content["text"] = text
        contents = [content]
        return self._embed(contents)

    def _embed(self, contents: list[dict]) -> list[float]:
        """通用嵌入方法。"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = self._build_request_body(contents)

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # 尝试阿里云百炼格式: output.embeddings[0].embedding
            if "output" in data:
                embeddings = data["output"].get("embeddings", [])
                if embeddings:
                    return embeddings[0]["embedding"]

            # 通用格式: data[0].embedding
            if "data" in data and data["data"]:
                return data["data"][0]["embedding"]

            raise ValueError(f"Invalid response format: {data}")
