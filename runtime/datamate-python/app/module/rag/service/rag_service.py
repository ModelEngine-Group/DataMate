import os
from typing import Optional

from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.knowledge_gen import KnowledgeBase
from app.db.session import get_db
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore import VectorStoreFactory
from .graph_rag import (
    DEFAULT_WORKING_DIR,
    build_embedding_func,
    build_llm_model_func,
    initialize_rag,
)
from ...system.service.common_service import get_model_by_id

logger = get_logger(__name__)

RAG_DOCUMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "根据以下上下文回答问题。如果上下文中没有相关信息，请说明。\n\n上下文：\n{context}"),
    ("human", "{input}"),
])


class RAGService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.rag = None

    async def init_graph_rag(self, knowledge_base_id: str):
        """初始化知识图谱 RAG 实例（用于查询）"""
        kb = await self._get_knowledge_base(knowledge_base_id)
        embedding_model = await self._get_models(kb.embedding_model)
        chat_model = await self._get_models(kb.chat_model)

        llm_callable = await build_llm_model_func(
            chat_model.model_name, chat_model.base_url, chat_model.api_key
        )
        from app.module.shared.llm import LLMFactory
        embedding_callable = await build_embedding_func(
            embedding_model.model_name,
            embedding_model.base_url,
            embedding_model.api_key,
            embedding_dim=LLMFactory.get_embedding_dimension(
                embedding_model.model_name, embedding_model.base_url, embedding_model.api_key
            ),
        )

        kb_working_dir = os.path.join(DEFAULT_WORKING_DIR, kb.name)
        self.rag = await initialize_rag(
            llm_callable, embedding_callable, kb_working_dir
        )

        return {"status": "initialized", "knowledge_base_id": knowledge_base_id}

    async def _get_knowledge_base(self, knowledge_base_id: str):
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        knowledge_base = result.scalars().first()
        if not knowledge_base:
            raise ValueError(f"Knowledge base with ID {knowledge_base_id} not found.")
        return knowledge_base

    async def _get_models(self, model_id: Optional[str]):
        if not model_id:
            raise ValueError("Model ID is required for initializing RAG.")
        models = await get_model_by_id(self.db, model_id)
        if not models:
            raise ValueError(f"Models with ID {model_id} not found.")
        return models

    async def query_rag(self, query: str, knowledge_base_id: str) -> str:
        kb = await self._get_knowledge_base(knowledge_base_id)
        if kb.type and str(kb.type).upper() == "GRAPH":
            if not self.rag:
                await self.init_graph_rag(knowledge_base_id)
            return await self.rag.get_knowledge_graph(query)
        # DOCUMENT 类型：LangChain Milvus 检索 + RAG
        return await self._query_document_rag(query, kb)

    async def _query_document_rag(self, query: str, kb: KnowledgeBase) -> str:
        """基于 Milvus 向量存储的检索与生成（混合检索 + LLM）。"""
        from langchain_classic.chains.combine_documents import (
            create_stuff_documents_chain,
        )
        from langchain_classic.chains.retrieval import create_retrieval_chain

        embedding_entity = await self._get_models(kb.embedding_model)
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
            model_type=embedding_entity.type,
        )
        vectorstore = VectorStoreFactory.create(
            collection_name=kb.name,
            embedding=embedding,
        )
        retriever = vectorstore.as_retriever(
            search_type="hybrid",
            search_kwargs={"k": 5},
        )
        chat_model_entity = await self._get_models(kb.chat_model)
        llm = ChatOpenAI(
            model=chat_model_entity.model_name,
            base_url=getattr(chat_model_entity, "base_url", None) or None,
            api_key=getattr(chat_model_entity, "api_key", None) or None,
        )
        combine_chain = create_stuff_documents_chain(llm, RAG_DOCUMENT_PROMPT)
        chain = create_retrieval_chain(retriever, combine_chain)
        result = await chain.ainvoke({"input": query})
        return result.get("answer", "")

    async def index(self, documents: list[dict], knowledge_base_id: int) -> dict:
        kb = await self._get_knowledge_base(str(knowledge_base_id))
        embedding_entity = await self._get_models(kb.embedding_model)
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
            model_type=embedding_entity.type,
        )
        vectorstore = VectorStoreFactory.create(
            collection_name=kb.name,
            embedding=embedding,
        )
        from langchain_core.documents import Document

        docs = [
            Document(
                page_content=doc.get("content", ""), metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        await vectorstore.aadd_documents(docs)
        logger.info(
            f"Indexed {len(documents)} documents into knowledge base {knowledge_base_id}"
        )
        return {"indexed_count": len(documents), "collection_name": kb.name}
