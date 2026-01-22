from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.model_config import ModelConfig


async def get_model_by_id(db: AsyncSession, model_id: str) -> Optional[ModelConfig]:
    """根据模型ID获取 ModelConfig 记录。"""
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
    return result.scalar_one_or_none()


def get_chat_client(model: ModelConfig) -> BaseChatModel:
    return ChatOpenAI(
        model=model.model_name,
        base_url=model.base_url,
        api_key=SecretStr(model.api_key),
    )


def chat(model: BaseChatModel, prompt: str) -> str:
    """使用指定模型进行聊天"""
    response = model.invoke(prompt)
    return response.content


# 实例化对象
def get_openai_client(model: ModelConfig) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=model.model_name,
        base_url=model.base_url,
        api_key=SecretStr(model.api_key),
    )

# 获取嵌入向量维度
def get_embedding_dimension(model: OpenAIEmbeddings) -> int:
    """获取 OpenAI 模型的嵌入向量维度"""
    return len(model.embed_query(model.model))
