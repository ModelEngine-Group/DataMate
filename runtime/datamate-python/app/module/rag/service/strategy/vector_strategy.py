"""
向量知识库策略

实现 DOCUMENT 类型知识库的检索和处理逻辑。
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pymilvus import AnnSearchRequest, Function, FunctionType

from app.core.exception import BusinessError, ErrorCodes
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore.milvus_client import get_milvus_client
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.response import PagedResponse, RagChunkResp
from app.module.rag.schema.request import ChunkFilterQuery
from app.module.rag.service.common import TextCleaner, MetadataBuilder, BatchProcessor, get_file_path
from app.module.system.service.common_service import get_model_by_id
from .base import KnowledgeBaseStrategy

logger = logging.getLogger(__name__)


class VectorKnowledgeBaseStrategy(KnowledgeBaseStrategy):
    """向量知识库策略实现

    提供 DOCUMENT 类型知识库的 query、 search 和 process_file 功能。
    """

    async def query(
        self,
        knowledge_base_id: str,
        **kwargs
    ) -> PagedResponse:
        """查询知识库分块数据（不涉及相似度计算）

        Args:
            knowledge_base_id: 知识库 ID
            **kwargs: 额外参数，必须包含:
                - rag_file_id: RAG 文件 ID
                - chunk_filter_query: 分页和过滤参数

        Returns:
            分页分块列表
        """
        rag_file_id = kwargs.get("rag_file_id")
        chunk_filter_query: ChunkFilterQuery = kwargs.get("chunk_filter_query")

        if not rag_file_id or not chunk_filter_query:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                "Missing rag_file_id or chunk_filter_query parameters"
            )

        kb_repo = KnowledgeBaseRepository(self.db)
        file_repo = RagFileRepository(self.db)

        knowledge_base = await kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        rag_file = await file_repo.get_by_id(rag_file_id)
        if not rag_file:
            raise BusinessError(ErrorCodes.RAG_FILE_NOT_FOUND)

        client = get_milvus_client()

        try:
            base_filter = f'metadata["rag_file_id"] == "{rag_file_id}"'
            combined_filter = self._build_combined_filter(base_filter, chunk_filter_query.expr)

            count_res = client.query(
                collection_name=knowledge_base.name,
                filter=combined_filter,
                output_fields=["id"],
            )
            total = len(count_res)

            offset = (chunk_filter_query.page - 1) * chunk_filter_query.size
            results = client.query(
                collection_name=knowledge_base.name,
                filter=combined_filter,
                output_fields=["id", "text", "metadata"],
                limit=chunk_filter_query.size,
                offset=offset,
            )

            chunks = [
                RagChunkResp(
                    id=item.get("id", ""),
                    text=item.get("text", ""),
                    metadata=item.get("metadata", {}),
                    score=0.0,
                    distance=None,
                )
                for item in results
            ]

            logger.info(
                "查询文件分块成功: kb=%s file=%s total=%d",
                knowledge_base_id, rag_file_id, total
            )

            return PagedResponse.create(
                content=chunks,
                total_elements=total,
                page=chunk_filter_query.page,
                size=chunk_filter_query.size,
            )

        except Exception as e:
            logger.error(
                "查询文件分块失败: kb=%s file=%s error=%s",
                knowledge_base_id, rag_file_id, e
            )
            raise BusinessError(
                ErrorCodes.RAG_MILVUS_ERROR,
                f"查询文件分块失败: {str(e)}"
            ) from e

    @staticmethod
    def _build_combined_filter(base_filter: str, user_expr: Optional[str]) -> str:
        if not user_expr:
            return base_filter
        return f"{base_filter} && {user_expr}"

    async def search(
        self,
        query_text: str,
        knowledge_base_ids: List[str],
        top_k: int = 10,
        threshold: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """基于输入文本的相似度检索（混合检索： 向量 + BM25)

        Args:
            query_text: 查询文本
            knowledge_base_ids: 知识库 ID 列表
            top_k: 返回结果数量
            threshold: 相似度阈值（可选)
            **kwargs: 额外参数

        Returns:
            统一格式的检索结果列表
        """
        kb_repo = KnowledgeBaseRepository(self.db)

        knowledge_bases = []
        for kb_id in knowledge_base_ids:
            kb = await kb_repo.get_by_id(kb_id)
            if not kb:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
            knowledge_bases.append(kb)

        embedding_entity = await get_model_by_id(self.db, knowledge_bases[0].embedding_model)
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

        try:
            query_vector = await asyncio.to_thread(embedding.embed_query, query_text)
        except Exception as e:
            logger.error("查询向量化失败: %s", e)
            raise BusinessError(
                ErrorCodes.RAG_EMBEDDING_FAILED,
                f"查询向量化失败: {str(e)}"
            ) from e

        all_results = await self._execute_hybrid_search(
            knowledge_bases, query_vector, query_text, top_k
        )

        all_results.sort(
            key=lambda x: x.get("score") or x.get("distance", 0),
            reverse=True
        )

        if threshold is not None:
            all_results = [
                r for r in all_results
                if (r.get("score") or r.get("distance", 0)) >= 0
            ]

        formatted = self._format_unified_results(all_results)
        logger.info("向量检索完成: 结果数=%d", len(formatted))
        return formatted

    @staticmethod
    async def _execute_hybrid_search(
        knowledge_bases: list,
        query_vector: list,
        query_text: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
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
                    }
                )
                search_results = client.hybrid_search(
                    collection_name=kb.name,
                    reqs=[dense_search, sparse_search],
                    ranker=ranker,
                    output_fields=["id", "text", "metadata"],
                    limit=top_k,
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

    @staticmethod
    def _format_unified_results(
        all_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """格式化为统一检索结果"""
        formatted = []
        for r in all_results:
            entity = r.get("entity", {})
            metadata = entity.get("metadata", {})
            if isinstance(metadata, dict):
                metadata_str = json.dumps(metadata, ensure_ascii=False)
            else:
                metadata_str = metadata if metadata else "{}"

            formatted.append({
                "id": entity.get("id", ""),
                "text": entity.get("text", ""),
                "score": r.get("score") or r.get("distance", 0),
                "metadata": json.loads(metadata_str) if isinstance(metadata_str, str) else metadata,
                "resultType": "vector",
                "knowledgeBaseId": r.get("knowledge_base_id", ""),
                "knowledgeBaseName": r.get("knowledge_base_name", ""),
            })

        return formatted

    async def process_file(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        **kwargs
    ) -> None:
        """处理单个文件（文档向量化)
        
        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            **kwargs: 额外参数
                - process_type: 分块类型
                - chunk_size: 分块大小
                - overlap_size: 重叠大小
                - delimiter: 分隔符
        """
        from pathlib import Path
        from app.module.rag.infra.vectorstore import VectorStoreFactory
        from app.module.rag.infra.document.processor import ingest_file_to_chunks
        from app.db.models.knowledge_gen import FileStatus
        from app.module.rag.service.common import TextCleaner, MetadataBuilder, BatchProcessor
        
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
                logger.error("文件解析失败，未生成任何分块")
                return
            
            valid_chunks = self._filter_and_clean_chunks(chunks)
            if not valid_chunks:
                await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED)
                await self.db.commit()
                logger.error("文件没有有效的分块内容")
                return
            
            embedding_entity = await get_model_by_id(self.db, kb.embedding_model)
            if not embedding_entity:
                raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)
            
            embedding = EmbeddingFactory.create_embeddings(
                model_name=str(embedding_entity.model_name),
                base_url=getattr(embedding_entity, "base_url", None),
                api_key=getattr(embedding_entity, "api_key", None),
            )
            
            vectorstore = VectorStoreFactory.create(
                collection_name=str(kb.name),
                embedding=embedding,
            )
            
            base_metadata = MetadataBuilder.build_chunk_metadata(rag_file, kb)
            MetadataBuilder.add_to_chunks(valid_chunks, base_metadata)
            
            await BatchProcessor.store_in_batches(vectorstore, valid_chunks)
            
            await file_repo.update_status(rag_file_id, FileStatus.PROCESSED)
            await file_repo.update_chunk_count(rag_file_id, len(valid_chunks))
            await self.db.commit()
            
            logger.info("文件 %s 向量化处理完成，分块数=%d", rag_file.file_name, len(valid_chunks))
            
        except Exception as e:
            logger.exception("文件 %s 处理失败: %s", rag_file.file_name, e)
            await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED)
            await self.db.commit()
            raise BusinessError(
                ErrorCodes.RAG_FILE_PROCESS_FAILED,
                f"文件处理失败: {str(e)}"
            ) from e
    
    def _get_file_path(self, rag_file) -> Optional[str]:
        from app.module.rag.service.common import get_file_path
        return get_file_path(rag_file)
    
    def _filter_and_clean_chunks(self, chunks: list) -> list:
        """过滤和清理分块"""
        from app.module.rag.service.common import TextCleaner
        
        valid_chunks = []
        for chunk in chunks:
            cleaned_text = TextCleaner.clean(chunk.text)
            
            if cleaned_text and TextCleaner.has_printable_content(cleaned_text):
                chunk.text = cleaned_text
                valid_chunks.append(chunk)
            else:
                logger.warning(
                    "跳过无效分块: chunk_index=%s",
                    chunk.metadata.get("chunk_index")
                )
        
        logger.info("有效分块数量: %d / %d", len(valid_chunks), len(chunks))
        return valid_chunks
    
    async def update_chunk(
        self,
        knowledge_base_id: str,
        chunk_id: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """更新指定分块的文本和元数据
        
        Args:
            knowledge_base_id: 知识库 ID
            chunk_id: 分块 ID
            text: 新的文本内容
            metadata: 新的元数据（可选）
        """
        from app.module.rag.infra.vectorstore import update_chunk_by_id
        
        kb_repo = KnowledgeBaseRepository(self.db)
        kb = await kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
        
        embedding_entity = await get_model_by_id(self.db, kb.embedding_model)
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)
        
        embedding = EmbeddingFactory.create_embeddings(
            model_name=str(embedding_entity.model_name),
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )
        
        await asyncio.to_thread(
            update_chunk_by_id,
            collection_name=str(kb.name),
            chunk_id=chunk_id,
            text=text,
            metadata=metadata,
            embedding_instance=embedding,
        )
        
        logger.info(
            "成功更新分块: kb=%s chunk_id=%s",
            knowledge_base_id, chunk_id
        )
    
    async def delete_chunk(
        self,
        knowledge_base_id: str,
        chunk_id: str,
    ) -> None:
        """删除指定分块
        
        Args:
            knowledge_base_id: 知识库 ID
            chunk_id: 分块 ID
        """
        from app.module.rag.infra.vectorstore import delete_chunk_by_id
        
        kb_repo = KnowledgeBaseRepository(self.db)
        kb = await kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
        
        await asyncio.to_thread(
            delete_chunk_by_id,
            collection_name=str(kb.name),
            chunk_id=chunk_id,
        )
        
        logger.info(
            "成功删除分块: kb=%s chunk_id=%s",
            knowledge_base_id, chunk_id
        )
