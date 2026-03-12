"""
知识图谱策略

实现 GRAPH 类型知识库的检索和处理逻辑。
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

import numpy as np
from lightrag import LightRAG
from lightrag.base import QueryParam
from lightrag.constants import DEFAULT_ENTITY_TYPES
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc, get_env_value, setup_logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exception import BusinessError, ErrorCodes
from app.db.models.knowledge_gen import KnowledgeBase
from app.module.rag.repository import KnowledgeBaseRepository
from app.module.rag.service.common import get_file_path
from app.module.system.service.common_service import get_model_by_id
from .base import KnowledgeBaseStrategy


setup_logger("lightrag", level="INFO")
logger = logging.getLogger(__name__)

DEFAULT_WORKING_DIR = str(settings.rag_storage_dir)


def _create_llm_func(model_name: str, base_url: str, api_key: str) -> Callable[..., Awaitable[str]]:
    async def _llm(prompt: str, system_prompt: str = None, history_messages: list = None, **kwargs) -> str:
        return await openai_complete_if_cache(
            model_name, prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            api_key=api_key, base_url=base_url, **kwargs,
        )
    return _llm


def _create_embedding_func(model_name: str, base_url: str, api_key: str, embedding_dim: int) -> EmbeddingFunc:
    async def _embed(texts: list[str]) -> np.ndarray:
        return await openai_embed.func(texts, model=model_name, api_key=api_key, base_url=base_url)
    return EmbeddingFunc(embedding_dim=embedding_dim, func=_embed, max_token_size=8192)


async def _create_rag(
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


class GraphKnowledgeBaseStrategy(KnowledgeBaseStrategy):
    # 类级别的缓存，允许跨实例共享
    _rag_cache: Dict[str, Any] = {}

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.kb_repo = KnowledgeBaseRepository(db)

    async def query(
        self,
        knowledge_base_id: str,
        **kwargs
    ) -> Any:
        node_label = kwargs.get("node_label")
        if not node_label:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                "Missing 'node_label' parameter for graph query"
            )

        kb = await self._get_knowledge_base(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        rag_instance = await self._get_or_create_graph_rag(kb)
        return await rag_instance.get_knowledge_graph(node_label=node_label)

    async def search(
        self,
        query_text: str,
        knowledge_base_ids: List[str],
        top_k: int = 10,
        threshold: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        if len(knowledge_base_ids) != 1:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                "At least one knowledge base required for graph search"
            )

        all_results = []
        for kb_id in knowledge_base_ids:
            kb = await self._get_knowledge_base(kb_id)
            if not kb:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

            rag_instance = await self._get_or_create_graph_rag(kb)
            # Use aquery_data for content retrieval (not get_knowledge_graph)
            query_param = QueryParam(mode="mix", top_k=top_k, only_need_context=True)
            retrieval_results = await rag_instance.aquery_data(query_text, query_param)

            unified_results = self._convert_retrieval_results_into_unified(
                retrieval_results, str(kb.id), str(kb.name)
            )
            all_results.extend(unified_results)

        all_results.sort(key=lambda x: x.get("score", 1.0), reverse=True)
        logger.info("知识图谱检索完成: 结果数=%d", len(all_results))
        return all_results

    @staticmethod
    def _convert_retrieval_results_into_unified(
        retrieval_results: Dict[str, Any],
        knowledge_base_id: str,
        knowledge_base_name: str
    ) -> List[Dict[str, Any]]:
        if not isinstance(retrieval_results, dict):
            return []

        data = retrieval_results.get("data", retrieval_results)
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])
        chunks = data.get("chunks", [])

        if not entities and not relationships and not chunks:
            return []

        reference_files: Dict[str, str] = {}
        ref_counter = 1

        for chunk in chunks:
            file_path = chunk.get("file_path", "")
            if file_path and file_path not in reference_files:
                reference_files[file_path] = str(ref_counter)
                ref_counter += 1

        for entity in entities:
            file_path = entity.get("file_path", "")
            if file_path and file_path not in reference_files:
                reference_files[file_path] = str(ref_counter)
                ref_counter += 1

        for rel in relationships:
            file_path = rel.get("file_path", "")
            if file_path and file_path not in reference_files:
                reference_files[file_path] = str(ref_counter)
                ref_counter += 1

        text_parts = []

        if entities:
            text_parts.append("\nKnowledge Graph Data (Entity):\n")
            text_parts.append("\n```json")
            for entity in entities:
                entity_data = {
                    "entity": entity.get("entity_name", ""),
                    "type": entity.get("entity_type", ""),
                    "description": entity.get("description", ""),
                }
                text_parts.append(f"\n{json.dumps(entity_data, ensure_ascii=False)}")
            text_parts.append("\n```")

        if relationships:
            text_parts.append("\n\nKnowledge Graph Data (Relationship):\n")
            text_parts.append("\n```json")
            for rel in relationships:
                rel_data = {
                    "entity1": rel.get("src_id", ""),
                    "entity2": rel.get("tgt_id", ""),
                    "description": rel.get("description", ""),
                }
                text_parts.append(f"\n{json.dumps(rel_data, ensure_ascii=False)}")
            text_parts.append("\n```")

        if chunks:
            text_parts.append(
                "\n\nDocument Chunks (Each entry has a reference_id refer to the `Reference Document List`):\n"
            )
            text_parts.append("\n```json")
            for chunk in chunks:
                file_path = chunk.get("file_path", "")
                ref_id = reference_files.get(file_path, "")
                chunk_data = {
                    "reference_id": ref_id,
                    "content": chunk.get("content", ""),
                }
                text_parts.append(f"\n{json.dumps(chunk_data, ensure_ascii=False)}")
            text_parts.append("\n```")

        if reference_files:
            text_parts.append(
                "\n\nReference Document List (Each entry starts with a [reference_id] "
                "that corresponds to entries in the Document Chunks):\n"
            )
            text_parts.append("\n```")
            for file_path, ref_id in reference_files.items():
                file_name = Path(file_path).name if file_path else ""
                text_parts.append(f"\n[{ref_id}] {file_name}")
            text_parts.append("\n```")

        formatted_text = "".join(text_parts)

        return [{
            "id": knowledge_base_id,
            "text": formatted_text,
            "score": 1.0,
            "metadata": {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "chunk_count": len(chunks),
                "reference_files": {v: k for k, v in reference_files.items()},
            },
            "resultType": "graph_retrieval",
            "knowledgeBaseId": knowledge_base_id,
            "knowledgeBaseName": knowledge_base_name,
        }]

    async def process_file(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        **kwargs
    ) -> None:
        from app.module.rag.infra.document.processor import ingest_file_to_chunks
        from app.db.models.knowledge_gen import FileStatus
        from app.module.rag.repository import RagFileRepository

        kb_repo = KnowledgeBaseRepository(self.db)
        file_repo = RagFileRepository(self.db)

        kb = await kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        rag_file = await file_repo.get_by_id(rag_file_id)
        if not rag_file:
            raise BusinessError(ErrorCodes.RAG_FILE_NOT_FOUND)

        try:
            await file_repo.update_status(rag_file_id, FileStatus.PROCESSING)
            await self.db.commit()

            file_path = get_file_path(rag_file)
            if not file_path or not Path(file_path).exists():
                await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED)
                await self.db.commit()
                logger.error("文件不存在: %s", file_path)
                return

            chunks = await ingest_file_to_chunks(
                file_path,
                process_type=kwargs.get("process_type", "DEFAULT_CHUNK"),
                chunk_size=kwargs.get("chunk_size", 500),
                overlap_size=kwargs.get("overlap_size", 50),
                delimiter=kwargs.get("delimiter"),
            )

            if not chunks:
                await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED)
                await self.db.commit()
                logger.error("文件解析失败，未生成任何文档")
                return

            rag_instance = await self._get_or_create_graph_rag(kb)

            for idx, chunk in enumerate(chunks):
                logger.info(
                    "插入文档到知识图谱: %s, 进度: %d/%d",
                    rag_file.file_name, idx + 1, len(chunks)
                )
                await rag_instance.ainsert(
                    input=chunk.text,
                    file_paths=[file_path]
                )

            await file_repo.update_status(rag_file_id, FileStatus.PROCESSED)
            await file_repo.update_chunk_count(rag_file_id, len(chunks))
            await self.db.commit()

            logger.info("文件 %s 知识图谱构建完成，文档数=%d", rag_file.file_name, len(chunks))

        except Exception as e:
            logger.exception("文件 %s 知识图谱构建失败: %s", rag_file.file_name, e)
            await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED)
            await self.db.commit()
            raise BusinessError(
                ErrorCodes.RAG_FILE_PROCESS_FAILED,
                f"知识图谱构建失败: {str(e)}"
            ) from e

    async def _get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        kb = await self.kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
        return kb

    async def _get_or_create_graph_rag(self, kb: KnowledgeBase) -> Any:
        kb_name = str(kb.name)
        if kb_name in self._rag_cache:
            return self._rag_cache[kb_name]

        chat_model = await get_model_by_id(self.db, str(kb.chat_model))
        embedding_model = await get_model_by_id(self.db, str(kb.embedding_model))

        if not chat_model or not embedding_model:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        llm_func = _create_llm_func(
            str(chat_model.model_name),
            str(chat_model.base_url),
            str(chat_model.api_key),
        )

        from app.module.shared.llm import LLMFactory
        embedding_func = _create_embedding_func(
            str(embedding_model.model_name),
            str(embedding_model.base_url),
            str(embedding_model.api_key),
            LLMFactory.get_embedding_dimension(
                str(embedding_model.model_name),
                str(embedding_model.base_url),
                str(embedding_model.api_key),
            ),
        )

        rag = await _create_rag(llm_func, embedding_func, DEFAULT_WORKING_DIR, workspace=kb_name)
        self._rag_cache[kb_name] = rag
        return rag

    @classmethod
    def rename_workspace(cls, old_name: str, new_name: str) -> None:
        old_path = Path(DEFAULT_WORKING_DIR) / old_name
        new_path = Path(DEFAULT_WORKING_DIR) / new_name
        if old_path.exists() and old_path.is_dir():
            old_path.rename(new_path)
            logger.info("知识图谱 workspace 重命名: %s -> %s", old_name, new_name)
        cls.clear_cache(old_name)

    @classmethod
    def clear_cache(cls, name: str) -> None:
        if name in cls._rag_cache:
            del cls._rag_cache[name]
            logger.info("已清除知识图谱缓存: %s", name)
