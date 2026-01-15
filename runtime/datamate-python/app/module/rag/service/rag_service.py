import os
import asyncio
from typing import Optional, Sequence

from fastapi import BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.dataset_management import DatasetFiles
from app.db.models.knowledge_gen import RagFile, RagKnowledgeBase
from app.db.models.model_config import ModelConfig
from app.db.session import get_db, AsyncSessionLocal
from app.module.shared.common.document_loaders import load_documents
from .graph_rag import (
    DEFAULT_WORKING_DIR,
    build_embedding_func,
    build_llm_model_func,
    initialize_rag,
)

logger = get_logger(__name__)


class RAGService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        background_tasks: BackgroundTasks | None = None,
    ):
        self.db = db
        self.background_tasks = background_tasks
        self.rag = None

    async def get_unprocessed_files(self, knowledge_base_id: str) -> Sequence[RagFile]:
        result = await self.db.execute(
            select(RagFile).where(
                RagFile.knowledge_base_id == knowledge_base_id,
                RagFile.status != "PROCESSED",
            )
        )
        return result.scalars().all()

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

        await self._schedule_file_processing(knowledge_base_id)

        return {"status": "initialized", "knowledge_base_id": knowledge_base_id}

    async def _schedule_file_processing(self, knowledge_base_id: str):
        if self.background_tasks is not None:
            self.background_tasks.add_task(self._process_with_fresh_session, knowledge_base_id, self.rag)
        else:
            asyncio.create_task(self._process_with_fresh_session(knowledge_base_id, self.rag))

    @staticmethod
    async def _process_with_fresh_session(knowledge_base_id: str, rag_instance):
        async with AsyncSessionLocal() as session:
            service = RAGService(session)
            service.rag = rag_instance
            await service._process_pending_files(knowledge_base_id)

    async def _process_pending_files(self, knowledge_base_id: str):
        rag_files = await self.get_unprocessed_files(knowledge_base_id)
        if not rag_files:
            logger.info(f"No pending files to process for knowledge base {knowledge_base_id}")
            return

        for rag_file in rag_files:
            await self._process_single_file(rag_file)

    async def _process_single_file(self, rag_file: RagFile):
        try:
            await self._mark_file_status(rag_file, "PROCESSING")
            dataset_file = await self._get_dataset_file(rag_file.file_id)
            documents = load_documents(dataset_file.file_path)
            for doc in documents:
                logger.info(f"Processing document {doc.page_content}")
                await self.rag.ainsert(input=doc.page_content, file_paths=[dataset_file.file_path])
        except Exception:  # noqa: BLE001
            logger.exception("Failed to process rag file %s", rag_file.id)
            await self._mark_file_status(rag_file, "PROCESS_FAILED")
            return
        await self._mark_file_status(rag_file, "PROCESSED")

    async def _get_dataset_file(self, file_id: str) -> DatasetFiles:
        result = await self.db.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        dataset_file = result.scalars().first()
        if not dataset_file:
            raise ValueError(f"Dataset file with ID {file_id} not found.")
        return dataset_file

    async def _mark_file_status(self, rag_file: RagFile, status: str):
        rag_file.status = status
        self.db.add(rag_file)
        await self.db.commit()
        await self.db.refresh(rag_file)

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

    async def query_rag(self, query: str, knowledge_base_id: str) -> str:
        if not self.rag:
            await self.init_graph_rag(knowledge_base_id)
        return await self.rag.get_knowledge_graph(query)
