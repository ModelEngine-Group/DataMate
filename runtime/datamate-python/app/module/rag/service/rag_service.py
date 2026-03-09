"""RAG 服务 - 支持向量检索和知识图谱两种模式"""
from typing import Optional

from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.knowledge_gen import KnowledgeBase, RagType
from app.db.session import get_db
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore import VectorStoreFactory
from .graph_rag import (
    DEFAULT_WORKING_DIR,
    create_embedding_func,
    create_llm_func,
    create_rag,
)
from ...system.service.common_service import get_model_by_id

logger = get_logger(__name__)

RAG_DOCUMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "根据以下上下文回答问题。如果上下文中没有相关信息，请说明。\n\n上下文：\n{context}"),
    ("human", "{input}"),
])

_rag_instances: dict[str, object] = {}


class RAGService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self._rag_cache: dict[str, object] = {}

    async def _get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        kb = result.scalars().first()
        if not kb:
            raise ValueError(f"Knowledge base {knowledge_base_id} not found")
        return kb

    async def _get_model(self, model_id: Optional[str]):
        if not model_id:
            raise ValueError("Model ID is required")
        model = await get_model_by_id(self.db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        return model

    async def _get_or_create_graph_rag(self, kb: KnowledgeBase):
        """获取或创建缓存的 Graph RAG 实例"""
        kb_name = str(kb.name)
        if kb_name in self._rag_cache:
            return self._rag_cache[kb_name]

        from app.module.shared.llm import LLMFactory

        chat_model = await self._get_model(kb.chat_model)
        embedding_model = await self._get_model(kb.embedding_model)

        llm_func = create_llm_func(
            str(chat_model.model_name),
            str(chat_model.base_url),
            str(chat_model.api_key),
        )
        embedding_func = create_embedding_func(
            str(embedding_model.model_name),
            str(embedding_model.base_url),
            str(embedding_model.api_key),
            LLMFactory.get_embedding_dimension(
                str(embedding_model.model_name),
                str(embedding_model.base_url),
                str(embedding_model.api_key),
            ),
        )

        import os
        working_dir = os.path.join(DEFAULT_WORKING_DIR, kb_name)
        rag = await create_rag(llm_func, embedding_func, working_dir, workspace=kb_name)
        self._rag_cache[kb_name] = rag
        return rag

    async def query_rag(self, query: str, knowledge_base_id: str):
        """查询 RAG（自动选择向量检索或知识图谱）"""
        kb = await self._get_knowledge_base(knowledge_base_id)

        if kb.type and str(kb.type).upper() == RagType.GRAPH:
            return await self._query_graph_rag(query, kb)

        return await self._query_document_rag(query, kb)

    async def _query_graph_rag(self, query: str, kb: KnowledgeBase):
        rag = await self._get_or_create_graph_rag(kb)
        return await rag.get_knowledge_graph(node_label=query)

    async def _query_document_rag(self, query: str, kb: KnowledgeBase) -> str:
        """向量检索查询"""
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
        from langchain_classic.chains.retrieval import create_retrieval_chain

        embedding_model = await self._get_model(kb.embedding_model)
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_model.model_name,
            base_url=getattr(embedding_model, "base_url", None),
            api_key=getattr(embedding_model, "api_key", None),
        )
        vectorstore = VectorStoreFactory.create(collection_name=kb.name, embedding=embedding)
        retriever = vectorstore.as_retriever(search_type="hybrid", search_kwargs={"k": 5})

        chat_model = await self._get_model(kb.chat_model)
        llm = ChatOpenAI(
            model=chat_model.model_name,
            base_url=getattr(chat_model, "base_url", None) or None,
            api_key=getattr(chat_model, "api_key", None) or None,
        )

        chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, RAG_DOCUMENT_PROMPT))
        result = await chain.ainvoke({"input": query})
        return result.get("answer", "")

    async def index(self, documents: list[dict], knowledge_base_id: int) -> dict:
        """索引文档到向量存储"""
        from langchain_core.documents import Document

        kb = await self._get_knowledge_base(str(knowledge_base_id))
        embedding_model = await self._get_model(kb.embedding_model)
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_model.model_name,
            base_url=getattr(embedding_model, "base_url", None),
            api_key=getattr(embedding_model, "api_key", None),
        )
        vectorstore = VectorStoreFactory.create(collection_name=kb.name, embedding=embedding)

        docs = [Document(page_content=doc.get("content", ""), metadata=doc.get("metadata", {})) for doc in documents]
        await vectorstore.aadd_documents(docs)
        logger.info(f"Indexed {len(documents)} documents into knowledge base {knowledge_base_id}")
        return {"indexed_count": len(documents), "collection_name": kb.name}
