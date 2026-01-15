import asyncio
import os
from typing import Awaitable, Callable, Optional

import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_embed, openai_complete_if_cache
from lightrag.utils import setup_logger, EmbeddingFunc

setup_logger("lightrag", level="DEBUG")
DEFAULT_WORKING_DIR = os.path.join(os.getcwd(), "rag_storage")


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
        return await openai_embed(
            texts,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            embedding_dim=embedding_dim,
        )

    return EmbeddingFunc(embedding_dim=embedding_dim, func=_embedding_func)


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
    )
    await rag.initialize_storages()
    return rag
