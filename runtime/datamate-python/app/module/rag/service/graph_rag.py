"""LightRAG 1.4.10 integration for knowledge graph RAG."""
import os
from typing import Awaitable, Callable

import numpy as np
from lightrag import LightRAG
from lightrag.constants import DEFAULT_ENTITY_TYPES
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc, get_env_value, setup_logger

from app.core.config import settings

setup_logger("lightrag", level="INFO")
DEFAULT_WORKING_DIR = str(settings.rag_storage_dir)


def create_llm_func(model_name: str, base_url: str, api_key: str) -> Callable[..., Awaitable[str]]:
    async def _llm(prompt: str, system_prompt: str = None, history_messages: list = None, **kwargs) -> str:
        return await openai_complete_if_cache(
            model_name, prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key, base_url=base_url, **kwargs,
        )
    return _llm


def create_embedding_func(model_name: str, base_url: str, api_key: str, embedding_dim: int) -> EmbeddingFunc:
    async def _embed(texts: list[str]) -> np.ndarray:
        return await openai_embed.func(texts, model=model_name, api_key=api_key, base_url=base_url)
    return EmbeddingFunc(embedding_dim=embedding_dim, func=_embed, max_token_size=8192)


async def create_rag(
    llm_func: Callable[..., Awaitable[str]],
    embedding_func: EmbeddingFunc,
    working_dir: str,
    workspace: str = "",
) -> LightRAG:
    os.makedirs(working_dir, exist_ok=True)
    rag = LightRAG(
        working_dir=working_dir,
        workspace=workspace,
        llm_model_func=llm_func,
        embedding_func=embedding_func,
        addon_params={
            "language": "Chinese",
            "entity_types": get_env_value("ENTITY_TYPES", DEFAULT_ENTITY_TYPES, list),
        },
    )
    await rag.initialize_storages()
    return rag


async def get_or_create_rag(
    knowledge_base_name: str,
    llm_func: Callable[..., Awaitable[str]],
    embedding_func: EmbeddingFunc,
) -> LightRAG:
    working_dir = os.path.join(DEFAULT_WORKING_DIR, knowledge_base_name)
    return await create_rag(llm_func, embedding_func, working_dir, workspace=knowledge_base_name)
