"""
检索服务

负责知识库内容的检索，支持向量 + BM25 混合检索。
"""
import logging
from typing import List

from pymilvus import MilvusClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exception import BusinessError, ErrorCodes
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.request import RetrieveReq, PagingQuery
from app.module.rag.schema.response import PagedResponse, RagChunkResp
from app.module.system.service.common_service import get_model_by_id

logger = logging.getLogger(__name__)


class RetrievalService:
    """检索服务类

    提供知识库内容的混合检索（向量 + BM25）和分块查询功能。
    """

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.file_repo = RagFileRepository(db)

    async def retrieve(self, request: RetrieveReq) -> List[dict]:
        """检索知识库内容（混合检索：向量 + BM25）

        Args:
            request: 检索请求

        Returns:
            检索结果列表

        Raises:
            BusinessError: 知识库不存在或嵌入模型不存在
        """
        import asyncio

        # 验证所有知识库存在
        knowledge_bases = []
        for kb_id in request.knowledge_base_ids:
            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
            knowledge_bases.append(kb)

        # 获取嵌入模型
        embedding_entity = await get_model_by_id(self.db, knowledge_bases[0].embedding_model)
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        # 创建嵌入模型实例
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

        # 生成查询向量
        try:
            query_vector = await asyncio.to_thread(embedding.embed_query, request.query)
        except Exception as e:
            logger.error("查询向量化失败: %s", e)
            raise BusinessError(ErrorCodes.RAG_EMBEDDING_FAILED, f"查询向量化失败: {str(e)}") from e

        # 执行混合检索
        all_results = await self._execute_hybrid_search(knowledge_bases, query_vector, request.query, request.top_k)

        # 按分数排序
        all_results.sort(key=lambda x: x.get("distance", 0), reverse=True)

        # 应用阈值过滤
        if request.threshold is not None:
            all_results = [r for r in all_results if r.get("distance", 0) >= request.threshold]

        # 格式化返回结果
        return self._format_results(all_results)

    async def _execute_hybrid_search(
        self,
        knowledge_bases: list,
        query_vector: list,
        query_text: str,
        top_k: int,
    ) -> List[dict]:
        """执行混合检索"""
        all_results = []
        token = getattr(settings, "milvus_token", None)
        client = MilvusClient(uri=settings.milvus_uri, token=token or "")

        for kb in knowledge_bases:
            try:
                if not client.has_collection(kb.name):
                    logger.warning("集合 %s 不存在，跳过", kb.name)
                    continue

                search_results = client.hybrid_search(
                    collection_name=kb.name,
                    data=[{"vector": query_vector, "sparse": query_text}],
                    anns_field=["vector", "sparse"],
                    limit=top_k,
                    ranker={"type": "weighted", "weights": [0.1, 0.9]},
                )

                if search_results and len(search_results) > 0:
                    for result in search_results[0]:
                        result["knowledge_base_id"] = kb.id
                        result["knowledge_base_name"] = kb.name
                        all_results.append(result)

            except Exception as e:
                logger.error("知识库 %s 混合检索失败: %s", kb.name, e)
                continue

        return all_results

    def _format_results(self, all_results: List[dict]) -> List[dict]:
        """格式化检索结果"""
        formatted = []
        for r in all_results:
            entity = r.get("entity", {})
            formatted.append({
                "id": entity.get("id", ""),
                "text": entity.get("text", ""),
                "metadata": entity.get("metadata", {}),
                "score": r.get("distance", 0),
                "knowledgeBaseId": r.get("knowledge_base_id", ""),
                "knowledgeBaseName": r.get("knowledge_base_name", ""),
            })

        logger.info("检索完成: 结果数=%d", len(formatted))
        return formatted

    async def get_chunks(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        paging_query: PagingQuery,
    ) -> PagedResponse:
        """获取指定 RAG 文件的分块列表

        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            paging_query: 分页参数

        Returns:
            分块列表（分页）
        """
        # 验证知识库和文件存在
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        rag_file = await self.file_repo.get_by_id(rag_file_id)
        if not rag_file:
            raise BusinessError(ErrorCodes.RAG_FILE_NOT_FOUND)

        # 查询 Milvus
        token = getattr(settings, "milvus_token", None)
        client = MilvusClient(uri=settings.milvus_uri, token=token or "")

        try:
            # 查询总数
            count_filter = f'metadata["rag_file_id"] == "{rag_file_id}"'
            count_res = client.query(
                collection_name=knowledge_base.name,
                filter=count_filter,
                output_fields=["id"],
            )
            total = len(count_res)

            # 查询分页数据
            offset = (paging_query.page - 1) * paging_query.size
            results = client.query(
                collection_name=knowledge_base.name,
                filter=count_filter,
                output_fields=["id", "text", "metadata"],
                limit=paging_query.size,
                offset=offset,
            )

            chunks = [
                RagChunkResp(
                    id=item.get("id", ""),
                    text=item.get("text", ""),
                    metadata=item.get("metadata", {}),
                    score=0.0,
                )
                for item in results
            ]

            logger.info("查询文件分块成功: kb=%s file=%s total=%d", knowledge_base_id, rag_file_id, total)

            return PagedResponse.create(
                content=chunks,
                total_elements=total,
                page=paging_query.page,
                size=paging_query.size,
            )

        except Exception as e:
            logger.error("查询文件分块失败: kb=%s file=%s error=%s", knowledge_base_id, rag_file_id, e)
            raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"查询文件分块失败: {str(e)}") from e
