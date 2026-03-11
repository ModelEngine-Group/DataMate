"""
知识图谱策略

实现 GRAPH 类型知识库的检索和处理逻辑。
"""
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exception import BusinessError, ErrorCodes
from app.db.models.knowledge_gen import KnowledgeBase
from app.module.rag.repository import KnowledgeBaseRepository
from app.module.rag.schema.response import UnifiedSearchResult
from app.module.system.service.common_service import get_model_by_id
from .base import KnowledgeBaseStrategy
from app.module.rag.service.graph_rag import (
    DEFAULT_WORKING_DIR,
    create_llm_func,
    create_embedding_func,
    create_rag,
    get_or_create_rag
)


logger = logging.getLogger(__name__)

_rag_cache: Dict[str, Any] = {}


class GraphKnowledgeBaseStrategy(KnowledgeBaseStrategy):
    """知识图谱策略实现

    提供 GRAPH 类型知识库的 query、 search 和 process_file 功能。
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.kb_repo = KnowledgeBaseRepository(db)
        self._rag_cache: Dict[str, Any] = {}

    async def query(
        self,
        knowledge_base_id: str,
        **kwargs
    ) -> Any:
        """查询知识图谱数据

        Args:
            knowledge_base_id: 知识库 ID
            **kwargs: 额外参数（如 node_label)

        Returns:
            知识图谱数据(格式由 LightRAG 定义)
        """
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
        """基于输入文本的相似度检索(知识图谱)

        Args:
            query_text: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            top_k: 返回结果数量
            threshold: 相似度阈值(可选)
            **kwargs: 额外参数

        Returns:
            统一格式的检索结果列表(UnifiedSearchResult)
        """
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
            graph_results = await rag_instance.get_knowledge_graph(node_label=query_text)

            unified_results = self._convert_graph_results_into_unified(
                graph_results, kb.id, kb.name
            )
            all_results.extend(unified_results)

        all_results.sort(key=lambda x: x.get("score", 1.0), reverse=True)
        logger.info("知识图谱检索完成: 结果数=%d", len(all_results))
        return all_results

    @staticmethod
    def _convert_graph_results_into_unified(
        graph_results: Any,
        knowledge_base_id: str,
        knowledge_base_name: str
    ) -> List[Dict[str, Any]]:
        """将 LightRAG 知识图谱结果转换为 UnifiedSearchResult"""
        results = []

        if isinstance(graph_results, dict):
            nodes = graph_results.get("nodes", [])
            edges = graph_results.get("edges", [])

            for node in nodes:
                results.append({
                    "id": node.get("id", ""),
                    "text": node.get("label", "") or node.get("description", ""),
                    "score": 1.0,
                    "metadata": node.get("metadata", {}),
                    "resultType": "graph",
                    "knowledgeBaseId": knowledge_base_id,
                    "knowledgeBaseName": knowledge_base_name,
                })

            for edge in edges:
                results.append({
                    "id": edge.get("id", ""),
                    "text": edge.get("label", "") or edge.get("description", ""),
                    "score": 1.0,
                    "metadata": edge.get("metadata", {}),
                    "resultType": "graph",
                    "knowledgeBaseId": knowledge_base_id,
                    "knowledgeBaseName": knowledge_base_name,
                })
        elif isinstance(graph_results, list):
            for item in graph_results:
                results.append({
                    "id": item.get("id", ""),
                    "text": item.get("label", "") or str(item),
                    "score": 1.0,
                    "metadata": item.get("metadata", {}),
                    "resultType": "graph",
                    "knowledgeBaseId": knowledge_base_id,
                    "knowledgeBaseName": knowledge_base_name,
                })

        return results

    async def process_file(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        **kwargs
    ) -> None:
        """处理单个文件(知识图谱构建)

        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            **kwargs: 鰃杂参数
        """
        from pathlib import Path
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

            file_path = self._get_file_path(rag_file)
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

    def _get_file_path(self, rag_file) -> Optional[str]:
        """获取文件路径"""
        from pathlib import Path

        if not rag_file.file_metadata:
            return None

        file_path = rag_file.file_metadata.get("file_path")
        if file_path:
            return str(Path(file_path).absolute())
        return None

    async def _get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        """获取知识库实体"""
        kb = await self.kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
        return kb

    async def _get_or_create_graph_rag(self, kb: KnowledgeBase) -> Any:
        """获取或创建缓存的 Graph RAG 实例"""
        kb_name = str(kb.name)
        if kb_name in self._rag_cache:
            return self._rag_cache[kb_name]

        chat_model = await get_model_by_id(self.db, kb.chat_model)
        embedding_model = await get_model_by_id(self.db, kb.embedding_model)

        if not chat_model or not embedding_model:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        llm_func = create_llm_func(
            str(chat_model.model_name),
            str(chat_model.base_url),
            str(chat_model.api_key),
        )

        from app.module.shared.llm import LLMFactory
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

        working_dir = os.path.join(DEFAULT_WORKING_DIR, kb_name)
        rag = await create_rag(llm_func, embedding_func, working_dir, workspace=kb_name)
        self._rag_cache[kb_name] = rag
        return rag
