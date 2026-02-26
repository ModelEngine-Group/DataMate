"""
ETL 服务

实现文件的异步 ETL 处理流程，使用 LangChain Milvus 向量存储（密集向量 + BM25 全文检索）。
对应 Java: com.datamate.rag.indexer.infra.event.RagEtlService
"""
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus
from app.module.rag.schema.request import AddFilesReq
from app.module.rag.repository import RagFileRepository, KnowledgeBaseRepository
from app.module.rag.infra.pipeline import ingest_file_to_chunks
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.milvus.factory import VectorStoreFactory
from app.module.rag.infra.milvus.vectorstore import (
    chunks_to_langchain_documents,
    create_java_compatible_collection,
    get_vector_dimension,
)
from app.module.system.service.common_service import get_model_by_id
from app.module.rag.infra.task.worker_pool import WorkerPool
from app.core.config import settings
from app.core.exception import BusinessError, ErrorCodes
from app.db.session import AsyncSessionLocal

import logging
import asyncio

logger = logging.getLogger(__name__)


class ETLService:
    """RAG ETL 服务类

    对应 Java: com.datamate.rag.indexer.infra.event.RagEtlService

    替代 Java 方案：
    - Java: @TransactionalEventListener + 虚拟线程 + 信号量
    - Python: asyncio + WorkerPool（信号量控制）

    功能：
    1. 解析文档（从共享文件系统读取）
    2. 分块
    3. 生成嵌入向量
    4. 存储到 Milvus
    5. 更新文件状态
    """

    def __init__(self, db: AsyncSession = None):
        """初始化服务

        Args:
            db: 数据库异步 session（可选，后台任务时会创建新的）
        """
        self.db = db
        self.worker_pool = WorkerPool(max_workers=10)

    async def process_files_background(
        self,
        knowledge_base_id: str,
        knowledge_base_name: str,
        request_data: dict
    ) -> None:
        """后台处理文件的入口方法（使用新的数据库 session）

        对应 Java 的 @TransactionalEventListener(phase = AFTER_COMMIT) + @Async

        Args:
            knowledge_base_id: 知识库 ID
            knowledge_base_name: 知识库名称
            request_data: 添加文件请求数据（dict 格式）
        """
        # 创建新的数据库 session
        async with AsyncSessionLocal() as db:
            try:
                file_repo = RagFileRepository(db)
                kb_repo = KnowledgeBaseRepository(db)

                # 获取知识库实体
                knowledge_base = await kb_repo.get_by_id(knowledge_base_id)
                if not knowledge_base:
                    logger.error(f"知识库不存在: {knowledge_base_id}")
                    return

                # 重建请求对象
                request = AddFilesReq.model_validate(request_data)

                # 获取待处理的文件
                files = await file_repo.get_unprocessed_files(knowledge_base_id)

                if not files:
                    logger.info(f"知识库 {knowledge_base_name} 没有待处理的文件")
                    return

                logger.info(f"开始处理 {len(files)} 个文件，知识库: {knowledge_base_name}")

                # 顺序处理文件（避免并发问题）
                for file in files:
                    try:
                        await self._process_single_file_with_session(
                            db, file, knowledge_base, request
                        )
                    except Exception as e:
                        logger.exception(f"文件 {file.file_name} 处理失败: {e}")
                        # 继续处理下一个文件

                logger.info(f"知识库 {knowledge_base_name} 文件处理完成")

            except Exception as e:
                logger.exception(f"后台处理文件失败: {e}")
            finally:
                await db.close()

    async def _process_single_file_with_session(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq
    ) -> None:
        """处理单个文件的 ETL 流程（使用提供的 session）

        Args:
            db: 数据库 session
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体
            request: 添加文件请求
        """
        file_repo = RagFileRepository(db)

        try:
            # 1. 更新状态为处理中
            await file_repo.update_status(rag_file.id, FileStatus.PROCESSING)
            await db.commit()

            # 2. 从 metadata 中获取文件路径和原始文件ID
            file_path = rag_file.file_metadata.get("file_path") if rag_file.file_metadata else None
            original_file_id = rag_file.file_id
            dataset_id = rag_file.file_metadata.get("dataset_id") if rag_file.file_metadata else None

            # 2.1 验证文件路径
            if not file_path:
                error_msg = f"文件路径未设置，file_metadata={rag_file.file_metadata}"
                logger.error(error_msg)
                await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg=error_msg)
                await db.commit()
                return

            # 2.2 确保使用绝对路径
            import os
            file_path = os.path.abspath(file_path)

            # 2.3 验证文件存在
            if not Path(file_path).exists():
                error_msg = f"文件不存在: {file_path}"
                logger.error(error_msg)
                await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg=error_msg)
                await db.commit()
                return

            # 3. 准备完整的 metadata（不包含 file_path，避免与函数参数冲突）
            file_extension = Path(file_path).suffix
            base_metadata = {
                "rag_file_id": rag_file.id,
                "original_file_id": original_file_id,
                "dataset_id": dataset_id,
                "file_name": rag_file.file_name,
                "file_extension": file_extension,
                "knowledge_base_id": knowledge_base.id,
                # file_path 不包含在此处，因为它作为位置参数传递
            }

            # 4. 加载并分块
            try:
                chunks = await ingest_file_to_chunks(
                    file_path,
                    process_type=request.process_type,
                    chunk_size=request.chunk_size,
                    overlap_size=request.overlap_size,
                    delimiter=request.delimiter,
                    **base_metadata
                )
            except Exception as e:
                error_msg = f"文档解析或分块失败: {str(e)}"
                logger.exception(f"文件 {rag_file.file_name} 解析失败: {e}")
                await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg=error_msg)
                await db.commit()
                return

            if not chunks:
                logger.warning(f"文件 {rag_file.file_name} 未生成任何分块")
                await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg="文档解析后未生成任何分块")
                await db.commit()
                return

            logger.info(f"文件 {rag_file.file_name} 分块完成，共 {len(chunks)} 个分块")

            # 5. 写入 Milvus 向量存储
            try:
                embedding_entity = await get_model_by_id(db, knowledge_base.embedding_model)
                if not embedding_entity:
                    raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

                # 5. 获取向量维度并创建集合
                try:
                    dimension = get_vector_dimension(
                        embedding_model=embedding_entity.model_name,
                        base_url=getattr(embedding_entity, "base_url", None),
                        api_key=getattr(embedding_entity, "api_key", None),
                    )
                    # 集合将由 VectorStoreFactory.create() 自动创建（如果已存在则删除）
                except BusinessError as e:
                    logger.warning("获取向量维度失败: %s", e)
                    raise

                embedding = EmbeddingFactory.create_embeddings(
                    model_name=embedding_entity.model_name,
                    base_url=getattr(embedding_entity, "base_url", None),
                    api_key=getattr(embedding_entity, "api_key", None),
                )
                vectorstore = VectorStoreFactory.create(
                    collection_name=knowledge_base.name,
                    embedding=embedding,
                )
                for c in chunks:
                    for key, value in base_metadata.items():
                        if key not in c.metadata:
                            c.metadata[key] = value
                ids = [str(uuid.uuid4()) for _ in chunks]
                documents, doc_ids = chunks_to_langchain_documents(chunks, ids=ids)
                vectorstore.add_documents(documents=documents, ids=doc_ids)

            except Exception as e:
                error_msg = f"向量化或存储到 Milvus 失败: {str(e)}"
                logger.exception(f"文件 {rag_file.file_name} 向量化失败: {e}")
                await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg=error_msg)
                await db.commit()
                return

            # 6. 更新文件状态为成功
            await file_repo.update_chunk_count(rag_file.id, len(chunks))
            await file_repo.update_status(rag_file.id, FileStatus.PROCESSED)
            await db.commit()

            logger.info(f"文件 {rag_file.file_name} ETL 处理完成")

        except Exception as e:
            logger.exception(f"文件 {rag_file.file_name} 处理失败: {e}")
            await file_repo.update_status(rag_file.id, FileStatus.PROCESS_FAILED, err_msg=str(e))
            await db.commit()

    async def process_files(
        self,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq
    ) -> None:
        """处理文件的入口方法（在事务提交后调用）- 已废弃，使用 process_files_background

        对应 Java 的 @TransactionalEventListener(phase = AFTER_COMMIT)

        Args:
            knowledge_base: 知识库实体
            request: 添加文件请求
        """
        logger.warning("process_files is deprecated, use process_files_background instead")
        # 这个方法保留用于兼容，但不推荐使用
        if not self.db:
            logger.error("No database session available")
            return

        file_repo = RagFileRepository(self.db)
        files = await file_repo.get_unprocessed_files(knowledge_base.id)

        if not files:
            logger.info(f"知识库 {knowledge_base.name} 没有待处理的文件")
            return

        logger.info(f"开始处理 {len(files)} 个文件，知识库: {knowledge_base.name}")

        for file in files:
            try:
                await self._process_single_file_with_session(self.db, file, knowledge_base, request)
            except Exception as e:
                logger.exception(f"文件 {file.file_name} 处理失败: {e}")
