import os
from typing import Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_gen import RagKnowledgeBase
from app.db.models.model_config import ModelConfig
from app.db.session import AsyncSessionLocal
from .graph_rag import (
    DEFAULT_WORKING_DIR,
    build_embedding_func,
    build_llm_model_func,
    initialize_rag,
)


class RAGService:
    def __init__(
        self,
        db: AsyncSession = Depends(AsyncSessionLocal),
    ):
        self.db = db
        self.rag = None


    async def get_unprocessed_files(self, knowledge_base_id: str) -> list[str]:
        pass

    async def init_graph_rag(self, knowledge_base_id: str):
        kb = await self._get_knowledge_base(knowledge_base_id)
        embedding_model = await self._get_model_config(kb.embedding_model)
        chat_model = await self._get_model_config(kb.chat_model)

        llm_callable = await build_llm_model_func(
            chat_model.model_name, chat_model.base_url, chat_model.api_key
        )
        embedding_callable = await build_embedding_func(
            embedding_model.model_name,
            embedding_model.base_url,
            embedding_model.api_key,
            embedding_dim=embedding_model.embedding_dim if hasattr(embedding_model, "embedding_dim") else 1024,
        )

        kb_working_dir = os.path.join(DEFAULT_WORKING_DIR, kb.name)
        self.rag = await initialize_rag(llm_callable, embedding_callable, kb_working_dir)
        return {"status": "initialized", "knowledge_base_id": knowledge_base_id}

    async def _get_knowledge_base(self, knowledge_base_id: str):
        result = await self.db.execute(
            select(RagKnowledgeBase).where(RagKnowledgeBase.id == knowledge_base_id)
        )
        knowledge_base = result.scalars().first()
        if not knowledge_base:
            raise ValueError(f"Knowledge base with ID {knowledge_base_id} not found.")
        return knowledge_base

    async def _get_model_config(self, model_id: Optional[str]):
        if not model_id:
            raise ValueError("Model ID is required for initializing RAG.")
        result = await self.db.execute(select(ModelConfig).where(ModelConfig.id == model_id))
        model = result.scalars().first()
        if not model:
            raise ValueError(f"Model config with ID {model_id} not found.")
        return model

