"""
检索服务

负责知识库内容的检索，支持向量 + BM25 混合检索。
"""

import json
import logging
from typing import List

from pymilvus import AnnSearchRequest, Function, FunctionType
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore.milvus_client import get_milvus_client
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.request import (
    RetrieveReq,
    PagingQuery,
    ImageRetrieveReq,
    ImageRetrieveReq,
)
from app.module.rag.schema.response import PagedResponse, RagChunkResp
from app.module.rag.service.multimodal_rerank_service import MultimodalRerankService
from app.module.system.service.common_service import get_model_by_id
from app.module.system.service.models_service import ModelsService

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
        models_service = ModelsService(db)
        self.rerank_service = MultimodalRerankService(models_service)

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
        embedding_entity = await get_model_by_id(
            self.db, knowledge_bases[0].embedding_model
        )
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        # 创建嵌入模型实例（传入模型类型）
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
            model_type=getattr(embedding_entity, "type", None),  # 传入模型类型
        )

        # 生成查询向量
        try:
            query_vector = await asyncio.to_thread(embedding.embed_query, request.query)
        except Exception as e:
            logger.error("查询向量化失败: %s", e)
            raise BusinessError(
                ErrorCodes.RAG_EMBEDDING_FAILED, f"查询向量化失败: {str(e)}"
            ) from e

        # 执行混合检索
        try:
            all_results = await self._execute_hybrid_search(
                knowledge_bases, query_vector, request.query, request.top_k
            )
        except Exception as e:
            logger.error(f"Milvus 检索失败: {str(e)}")
            # 如果 Milvus 连接失败，返回空结果而不是抛出异常
            if "Fail connecting to server" in str(
                e
            ) or "illegal connection params" in str(e):
                logger.warning(
                    "Milvus 服务不可用，请确保已启动 Milvus 服务（docker-compose --profile milvus up -d）"
                )
                return []
            raise BusinessError(
                ErrorCodes.RAG_MILVUS_ERROR, f"检索失败: {str(e)}"
            ) from e

        # 如果配置了重排序模型，执行重排序
        rerank_model_id = knowledge_bases[0].rerank_model
        if rerank_model_id:
            try:
                all_results = await self._apply_rerank(
                    request.query, all_results, rerank_model_id, request.top_k
                )
            except Exception as e:
                logger.warning(f"重排序失败，使用原始检索结果: {str(e)}")

        # 按分数排序
        all_results.sort(
            key=lambda x: x.get("score") or x.get("distance", 0), reverse=True
        )

        # 应用阈值过滤
        if request.threshold is not None:
            all_results = [
                r for r in all_results if (r.get("score") or r.get("distance", 0)) >= 0
            ]

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
        client = get_milvus_client()

        for kb in knowledge_bases:
            try:
                if not client.has_collection(kb.name):
                    logger.warning("集合 %s 不存在，跳过", kb.name)
                    continue

                dense_search = AnnSearchRequest(
                    data=[query_vector],
                    anns_field="vector",
                    param={"nprobe": 10},
                    limit=top_k,
                )

                sparse_search = AnnSearchRequest(
                    data=[query_text],
                    anns_field="sparse",
                    param={"drop_ratio_search": 0.2},
                    limit=top_k,
                )

                ranker = Function(
                    name="weight",
                    input_field_names=[],
                    function_type=FunctionType.RERANK,
                    params={
                        "reranker": "weighted",
                        "weights": [0.1, 0.9],
                        "norm_score": True,
                    },
                )
                search_results = client.hybrid_search(
                    collection_name=kb.name,
                    reqs=[dense_search, sparse_search],
                    ranker=ranker,
                    output_fields=["id", "text", "metadata"],
                    limit=top_k,
                )

                logger.info(f"----------, {search_results.__str__()}")

                if search_results and len(search_results) > 0:
                    for result in search_results[0]:
                        result["knowledge_base_id"] = kb.id
                        result["knowledge_base_name"] = kb.name
                        all_results.append(result)

            except Exception as e:
                logger.error("知识库 %s 混合检索失败: %s", kb.name, e)
                continue

        return all_results

    async def _apply_rerank(
        self,
        query: str,
        results: List[dict],
        rerank_model_id: str,
        top_k: int,
    ) -> List[dict]:
        """应用重排序

        Args:
            query: 查询文本
            results: 检索结果
            rerank_model_id: 重排序模型ID
            top_k: 返回前K个结果

        Returns:
            重排序后的结果
        """
        if not results:
            return results

        rerank_response = await self.rerank_service.rerank(
            query=query,
            results=results,
            rerank_model_id=rerank_model_id,
            top_k=min(top_k, len(results)),
            vision_model_id=None,  # TODO: 从知识库配置中获取视觉模型ID
        )

        # 根据重排序结果重新组织原始结果
        reranked_results = []
        for rerank_item in rerank_response.results:
            original_result = results[rerank_item.index]
            original_result["score"] = rerank_item.relevance_score
            original_result["content_type"] = rerank_item.content_type
            reranked_results.append(original_result)

        logger.info(
            f"重排序完成: 原始结果数={len(results)}, 重排序后结果数={len(reranked_results)}"
        )
        return reranked_results

    def _format_results(self, all_results: List[dict]) -> List[dict]:
        """格式化检索结果"""
        formatted = []
        for r in all_results:
            entity = r.get("entity", {})
            metadata = entity.get("metadata", {})
            if isinstance(metadata, dict):
                metadata_str = json.dumps(metadata, ensure_ascii=False)
            else:
                metadata_str = metadata if metadata else "{}"

            formatted.append(
                {
                    "entity": {
                        "metadata": metadata_str,
                        "text": entity.get("text", ""),
                        "id": entity.get("id", ""),
                    },
                    "score": r.get("score") or r.get("distance", 0),
                    "id": entity.get("id", ""),
                    "knowledgeBaseId": r.get("knowledge_base_id", ""),
                    "knowledgeBaseName": r.get("knowledge_base_name", ""),
                }
            )

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

        client = get_milvus_client()

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

            logger.info(
                "查询文件分块成功: kb=%s file=%s total=%d",
                knowledge_base_id,
                rag_file_id,
                total,
            )

            return PagedResponse.create(
                content=chunks,
                total_elements=total,
                page=paging_query.page,
                size=paging_query.size,
            )

        except Exception as e:
            logger.error(
                "查询文件分块失败: kb=%s file=%s error=%s",
                knowledge_base_id,
                rag_file_id,
                e,
            )
            raise BusinessError(
                ErrorCodes.RAG_MILVUS_ERROR, f"查询文件分块失败: {str(e)}"
            ) from e

    async def retrieve_by_image(self, request: "ImageRetrieveReq") -> List[dict]:
        """图片检索（以图搜图）

        参考 Java 版本 KnowledgeBaseService.retrieveByImage 实现

        Args:
            request: 图片检索请求

        Returns:
            检索结果列表

        Raises:
            BusinessError: 知识库不存在、模型不存在或嵌入失败
        """
        import asyncio

        # 验证知识库存在
        knowledge_bases = []
        for kb_id in request.knowledge_base_ids:
            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
            knowledge_bases.append(kb)

        # 获取嵌入模型
        embedding_entity = await get_model_by_id(
            self.db, knowledge_bases[0].embedding_model
        )
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        # 验证是多模态嵌入模型
        if embedding_entity.type != "MULTIMODAL_EMBEDDING":
            raise BusinessError(
                ErrorCodes.RAG_MODEL_NOT_FOUND, "图片检索需要多模态嵌入模型支持"
            )

        # 创建多模态嵌入模型实例
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
            model_type=embedding_entity.type,
        )

        # 生成图片向量
        try:
            query_vector = await asyncio.to_thread(
                embedding.embed_image, request.image_url, request.query_text or ""
            )
        except Exception as e:
            logger.error("图片向量化失败: %s", e)
            raise BusinessError(
                ErrorCodes.RAG_EMBEDDING_FAILED, f"图片向量化失败: {str(e)}"
            ) from e

        # 执行向量检索（仅向量检索，不使用 BM25）
        try:
            all_results = await self._execute_vector_search(
                knowledge_bases, query_vector, request.top_k
            )
        except Exception as e:
            logger.error(f"Milvus 图片检索失败: {str(e)}")
            if "Fail connecting to server" in str(
                e
            ) or "illegal connection params" in str(e):
                logger.warning("Milvus 服务不可用，请确保已启动 Milvus 服务")
                return []
            raise BusinessError(
                ErrorCodes.RAG_MILVUS_ERROR, f"图片检索失败: {str(e)}"
            ) from e

        # 如果配置了重排序模型，执行重排序
        rerank_model_id = knowledge_bases[0].rerank_model
        if rerank_model_id:
            try:
                # 图片检索使用 query_text 作为重排序查询
                query_for_rerank = request.query_text or "[图片检索]"
                all_results = await self._apply_rerank(
                    query_for_rerank, all_results, rerank_model_id, request.top_k
                )
            except Exception as e:
                logger.warning(f"重排序失败，使用原始检索结果: {str(e)}")

        # 按分数排序
        all_results.sort(
            key=lambda x: x.get("score") or x.get("distance", 0), reverse=True
        )

        # 格式化返回结果
        return self._format_results(all_results)

    async def _execute_vector_search(
        self,
        knowledge_bases: list,
        query_vector: list,
        top_k: int,
    ) -> List[dict]:
        """执行纯向量检索（用于图片检索）

        Args:
            knowledge_bases: 知识库列表
            query_vector: 查询向量
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        all_results = []
        client = get_milvus_client()

        for kb in knowledge_bases:
            try:
                if not client.has_collection(kb.name):
                    logger.warning("集合 %s 不存在，跳过", kb.name)
                    continue

                # 执行向量检索
                search_results = client.search(
                    collection_name=kb.name,
                    data=[query_vector],
                    anns_field="vector",
                    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
                    limit=top_k,
                    output_fields=["id", "text", "metadata"],
                )

                if search_results and len(search_results) > 0:
                    for result in search_results[0]:
                        result["knowledge_base_id"] = kb.id
                        result["knowledge_base_name"] = kb.name
                        all_results.append(result)

            except Exception as e:
                logger.error("知识库 %s 向量检索失败: %s", kb.name, e)
                continue

        return all_results
