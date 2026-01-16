import os
from pathlib import Path
from typing import Awaitable, Callable, Optional
from app.core.config import settings

import numpy as np
from lightrag import LightRAG
from lightrag.constants import DEFAULT_ENTITY_TYPES
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import openai_embed, openai_complete_if_cache
from lightrag.utils import setup_logger, EmbeddingFunc, get_env_value

setup_logger("lightrag", level="INFO")
DEFAULT_WORKING_DIR = Path(settings.rag_storage_dir)


async def build_llm_model_func(model_name: str, base_url: str, api_key: str) -> Callable[..., Awaitable[str]]:
    async def _llm_model(
        prompt, system_prompt=None, history_messages=None, **kwargs
    ) -> str:
        history_messages = history_messages or []
        return await openai_complete_if_cache(
            model_name,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )

    return _llm_model


async def build_embedding_func(
    model_name: str, base_url: str, api_key: str, embedding_dim: int
) -> EmbeddingFunc:
    async def _embedding_func(texts: list[str]) -> np.ndarray:
        return await openai_embed.func(
            texts,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        )

    return EmbeddingFunc(embedding_dim=embedding_dim, func=_embedding_func, max_token_size=8192)


async def initialize_rag(
    llm_callable: Callable[..., Awaitable[str]],
    embedding_callable: EmbeddingFunc,
    working_dir: Optional[str] = None,
):
    target_dir = working_dir or DEFAULT_WORKING_DIR
    os.makedirs(target_dir, exist_ok=True)
    rag = LightRAG(
        working_dir=target_dir,
        llm_model_func=llm_callable,
        embedding_func=embedding_callable,
        addon_params={
            "language": "Chinese",
            "entity_types": get_env_value("ENTITY_TYPES", DEFAULT_ENTITY_TYPES, list),
        }
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag
