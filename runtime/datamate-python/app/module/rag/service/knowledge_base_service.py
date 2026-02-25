"""
知识库业务服务

实现知识库的 CRUD 操作和业务逻辑
对应 Java: com.datamate.rag.indexer.application.KnowledgeBaseService
"""
import logging
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.core.config import settings
from app.module.rag.infra.milvus.vectorstore import drop_collection, rename_collection
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.db.models.knowledge_gen import KnowledgeBase
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.request import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseUpdateReq,
    KnowledgeBaseQueryReq,
    AddFilesReq,
    DeleteFilesReq,
    RagFileReq,
    RetrieveReq,
    PagingQuery,
)
from app.module.rag.schema.response import KnowledgeBaseResp, PagedResponse, RagChunkResp, RagFileResp
from app.module.rag.service.etl_service import ETLService
from app.module.rag.service.file_service import FileService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库业务服务类

    对应 Java: com.datamate.rag.indexer.application.KnowledgeBaseService

    功能：
    1. 知识库 CRUD 操作
    2. 文件管理
    3. 检索功能
    """

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.file_repo = RagFileRepository(db)
        self.file_service = FileService(db)
        self.etl_service = ETLService(db)

    async def create(self, request: KnowledgeBaseCreateReq) -> str:
        """创建知识库

        对应 Java: create 方法

        Args:
            request: 创建请求

        Returns:
            知识库 ID

        Raises:
            BusinessError: 知识库名称已存在
        """
        # 创建知识库实体
        knowledge_base = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            type=request.type,
            embedding_model=request.embedding_model,
            chat_model=request.chat_model
        )

        # 保存到数据库
        knowledge_base = await self.kb_repo.create(knowledge_base)

        # Milvus 集合由 LangChain Milvus 在首次 ETL add_documents 时自动创建（含 BM25 全文检索）
        logger.info(f"成功创建知识库: {request.name}")

        # 提交事务
        await self.db.commit()

        return knowledge_base.id

    async def update(self, knowledge_base_id: str, request: KnowledgeBaseUpdateReq) -> None:
        """更新知识库

        对应 Java: update 方法

        Args:
            knowledge_base_id: 知识库 ID
            request: 更新请求

        Raises:
            BusinessError: 知识库不存在
        """
        # 获取现有知识库
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        old_name = knowledge_base.name

        # 更新字段
        knowledge_base.name = request.name
        knowledge_base.description = request.description

        # 更新数据库
        await self.kb_repo.update(knowledge_base)

        # 如果名称变更，重命名 Milvus 集合
        if old_name != request.name:
            try:
                rename_collection(old_name, request.name)
            except BusinessError:
                await self.db.rollback()
                raise

        await self.db.commit()

    async def delete(self, knowledge_base_id: str) -> None:
        """删除知识库

        对应 Java: delete 方法

        Args:
            knowledge_base_id: 知识库 ID

        Raises:
            BusinessError: 知识库不存在
        """
        # 获取知识库
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 删除所有文件
        await self.file_repo.delete_by_knowledge_base(knowledge_base_id)

        # 删除知识库
        await self.kb_repo.delete(knowledge_base_id)

        # 删除 Milvus 集合
        try:
            drop_collection(knowledge_base.name)
        except Exception as e:
            logger.error("删除 Milvus 集合失败: %s", e)

        await self.db.commit()

    async def get_by_id(self, knowledge_base_id: str) -> KnowledgeBaseResp:
        """获取知识库详情

        对应 Java: getById 方法

        Args:
            knowledge_base_id: 知识库 ID

        Returns:
            知识库响应对象

        Raises:
            BusinessError: 知识库不存在
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 统计文件数量
        file_count = await self.file_repo.count_by_knowledge_base(knowledge_base_id)
        chunk_count = await self.file_repo.count_chunks_by_knowledge_base(knowledge_base_id)

        response = KnowledgeBaseResp(
            id=knowledge_base.id,
            name=knowledge_base.name,
            description=knowledge_base.description,
            type=knowledge_base.type,
            embedding_model=knowledge_base.embedding_model,
            chat_model=knowledge_base.chat_model,
            file_count=file_count,
            chunk_count=chunk_count,
            created_at=knowledge_base.created_at,
            updated_at=knowledge_base.updated_at,
            created_by=knowledge_base.created_by,
            updated_by=knowledge_base.updated_by
        )

        return response

    async def list(self, request: KnowledgeBaseQueryReq) -> PagedResponse:
        """分页查询知识库列表

        对应 Java: list 方法

        Args:
            request: 查询请求

        Returns:
            分页响应
        """
        items, total = await self.kb_repo.list(
            keyword=request.keyword,
            rag_type=request.type,
            page=request.page,
            page_size=request.page_size
        )

        # 转换为响应对象
        responses = []
        for item in items:
            file_count = await self.file_repo.count_by_knowledge_base(item.id)
            chunk_count = await self.file_repo.count_chunks_by_knowledge_base(item.id)

            response = KnowledgeBaseResp(
                id=item.id,
                name=item.name,
                description=item.description,
                type=item.type,
                embedding_model=item.embedding_model,
                chat_model=item.chat_model,
                file_count=file_count,
                chunk_count=chunk_count,
                created_at=item.created_at,
                updated_at=item.updated_at,
                created_by=item.created_by,
                updated_by=item.updated_by
            )
            responses.append(response)

        return PagedResponse.create(
            content=responses,
            total_elements=total,
            page=request.page,
            size=request.page_size
        )

    async def add_files(self, request: AddFilesReq) -> dict:
        """添加文件到知识库

        对应 Java: addFiles 方法

        Args:
            request: 添加文件请求

        Returns:
            包含成功和跳过文件数量的字典

        Raises:
            BusinessError: 知识库不存在
        """
        # 验证知识库存在
        knowledge_base = await self.kb_repo.get_by_id(request.knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 添加文件记录
        rag_files, skipped_file_ids = await self.file_service.add_files(request)

        # 提交事务后触发 ETL 处理
        await self.db.commit()

        # 异步处理文件（在事务提交后）
        if rag_files:
            await self.etl_service.process_files(knowledge_base, request)

        return {
            "success_count": len(rag_files),
            "skipped_count": len(skipped_file_ids),
            "skipped_file_ids": skipped_file_ids
        }

    async def list_files(
        self,
        knowledge_base_id: str,
        request: RagFileReq
    ) -> PagedResponse:
        """获取知识库文件列表

        对应 Java: listFiles 方法

        Args:
            knowledge_base_id: 知识库 ID
            request: 查询请求

        Returns:
            分页响应

        Raises:
            BusinessError: 知识库不存在
        """
        # 验证知识库存在
        if not await self.kb_repo.get_by_id(knowledge_base_id):
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        items, total = await self.file_repo.list_by_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            keyword=request.keyword,
            status=request.status,
            page=request.page,
            page_size=request.page_size
        )

        # 转换为响应对象
        responses = [RagFileResp(
            id=item.id,
            knowledge_base_id=item.knowledge_base_id,
            file_name=item.file_name,
            file_id=item.file_id,
            chunk_count=item.chunk_count,
            metadata=item.file_metadata,
            status=item.status,
            err_msg=item.err_msg,
            created_at=item.created_at,
            updated_at=item.updated_at,
            created_by=item.created_by,
            updated_by=item.updated_by
        ) for item in items]

        return PagedResponse.create(
            content=responses,
            total_elements=total,
            page=request.page,
            size=request.page_size
        )

    async def delete_files(self, knowledge_base_id: str, request: DeleteFilesReq) -> None:
        """删除知识库文件

        对应 Java: deleteFiles 方法

        Args:
            knowledge_base_id: 知识库 ID
            request: 删除文件请求

        Raises:
            BusinessError: 知识库不存在
        """
        # 验证知识库存在
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 删除文件（包括 Milvus 数据）
        await self.file_service.delete_files(knowledge_base_id, request.file_ids)

        await self.db.commit()

    async def retrieve(self, request: RetrieveReq) -> List[dict]:
        """检索知识库内容

        对应 Java: retrieve 方法

        使用混合检索（向量 + BM25）

        Args:
            request: 检索请求

        Returns:
            检索结果列表

        Raises:
            BusinessError: 知识库不存在
        """
        import asyncio

        # 1. 验证所有知识库存在
        knowledge_bases = []
        for kb_id in request.knowledge_base_ids:
            kb = await self.kb_repo.get_by_id(kb_id)
            if not kb:
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)
            knowledge_bases.append(kb)

        # 2. 获取嵌入模型（使用第一个知识库的配置）
        embedding_entity = await get_model_by_id(self.db, knowledge_bases[0].embedding_model)
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        # 3. 创建嵌入模型实例
        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

        # 4. 生成查询向量
        try:
            query_vector = await asyncio.to_thread(embedding.embed_query, request.query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise BusinessError(ErrorCodes.RAG_EMBEDDING_FAILED, f"查询向量化失败: {str(e)}") from e

        # 5. 执行混合检索（向量 + BM25）
        from pymilvus import MilvusClient

        all_results = []

        try:
            client = MilvusClient(uri=settings.milvus_uri)

            for kb in knowledge_bases:
                try:
                    # 检查集合是否存在
                    if not client.has_collection(kb.name):
                        logger.warning(f"Collection {kb.name} does not exist, skipping")
                        continue

                    # 混合检索：密集向量 + 稀疏向量（BM25）
                    search_results = client.hybrid_search(
                        collection_name=kb.name,
                        data=[
                            {
                                "vector": query_vector,
                                "sparse": request.query
                            }
                        ],
                        anns_field=["vector", "sparse"],
                        limit=request.top_k,
                        ranker={
                            "type": "weighted",
                            "weights": [0.1, 0.9]  # 10% 向量相似度，90% BM25 关键词匹配
                        }
                    )

                    # 提取结果
                    if search_results and len(search_results) > 0:
                        for result in search_results[0]:
                            result["knowledge_base_id"] = kb.id
                            result["knowledge_base_name"] = kb.name
                            all_results.append(result)

                except Exception as e:
                    logger.error(f"Hybrid search failed for kb {kb.name}: {e}")
                    # 继续处理其他知识库
                    continue

        except Exception as e:
            logger.error(f"Milvus client initialization or search failed: {e}")
            raise BusinessError(ErrorCodes.RAG_MILVUS_ERROR, f"检索失败: {str(e)}") from e

        # 6. 按分数降序排序
        all_results.sort(key=lambda x: x.get("distance", 0), reverse=True)

        # 7. 应用阈值过滤
        if request.threshold is not None:
            all_results = [r for r in all_results if r.get("distance", 0) >= request.threshold]

        # 8. 格式化返回结果
        formatted_results = []
        for r in all_results:
            entity = r.get("entity", {})
            formatted_results.append({
                "id": entity.get("id", ""),
                "text": entity.get("text", ""),
                "metadata": entity.get("metadata", {}),
                "score": r.get("distance", 0),
                "knowledgeBaseId": r.get("knowledge_base_id", ""),
                "knowledgeBaseName": r.get("knowledge_base_name", "")
            })

        logger.info(f"Retrieve completed: query='{request.query}' results={len(formatted_results)}")
        return formatted_results

    async def get_chunks(
        self,
        knowledge_base_id: str,
        rag_file_id: str,
        paging_query: PagingQuery
    ) -> PagedResponse:
        """获取指定 RAG 文件的分块列表

        对应 Java: getChunks 方法

        从 Milvus 查询指定 rag_file_id 的分块，支持分页。

        Args:
            knowledge_base_id: 知识库 ID
            rag_file_id: RAG 文件 ID
            paging_query: 分页参数

        Returns:
            分块列表（分页）
        """
        # 验证知识库存在
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 验证文件存在
        rag_file = await self.file_repo.get_by_id(rag_file_id)
        if not rag_file:
            raise BusinessError(ErrorCodes.RAG_FILE_NOT_FOUND)

        # 使用 MilvusClient 查询指定文件的分块
        from pymilvus import MilvusClient

        from app.core.exception import BusinessError as BE, ErrorCodes as EC

        try:
            conn_args = settings.milvus_uri
            token = getattr(settings, "milvus_token", None)
            client = MilvusClient(uri=conn_args, token=token)

            # 查询总数
            count_filter_expr = f'metadata["rag_file_id"] == "{rag_file_id}"'
            count_res = client.query(
                collection_name=knowledge_base.name,
                filter=count_filter_expr,
                output_fields=["id"]
            )
            total = len(count_res)

            # 查询分页数据
            offset = (paging_query.page - 1) * paging_query.size
            filter_expr = f'metadata["rag_file_id"] == "{rag_file_id}"'
            results = client.query(
                collection_name=knowledge_base.name,
                filter=filter_expr,
                output_fields=["id", "text", "metadata"],
                limit=paging_query.size,
                offset=offset
            )

            # 转换为 RagChunkResp
            chunks = []
            for item in results:
                chunks.append(RagChunkResp(
                    id=item.get("id", ""),
                    text=item.get("text", ""),
                    metadata=item.get("metadata", {}),
                    score=0.0  # 非相似度查询，默认分数为 0
                ))

            logger.info(
                "查询文件分块成功: kb=%s file=%s total=%d page=%d size=%d",
                knowledge_base_id, rag_file_id, total, paging_query.page, paging_query.size
            )

            return PagedResponse.create(
                content=chunks,
                total_elements=total,
                page=paging_query.page,
                size=paging_query.size
            )

        except Exception as e:
            logger.error("查询文件分块失败: kb=%s file=%s error=%s", knowledge_base_id, rag_file_id, e)
            raise BE(EC.RAG_MILVUS_ERROR, f"查询文件分块失败: {str(e)}") from e

