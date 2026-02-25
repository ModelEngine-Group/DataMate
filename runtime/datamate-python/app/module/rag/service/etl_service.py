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

import logging

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

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.file_repo = RagFileRepository(db)
        self.kb_repo = KnowledgeBaseRepository(db)
        self.worker_pool = WorkerPool(max_workers=10)

    async def process_files(
        self,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq
    ) -> None:
        """处理文件的入口方法（在事务提交后调用）

        对应 Java 的 @TransactionalEventListener(phase = AFTER_COMMIT)

        Args:
            knowledge_base: 知识库实体
            request: 添加文件请求
        """
        # 获取待处理的文件
        files = await self.file_repo.get_unprocessed_files(knowledge_base.id)

        if not files:
            logger.info(f"知识库 {knowledge_base.name} 没有待处理的文件")
            return

        logger.info(f"开始处理 {len(files)} 个文件，知识库: {knowledge_base.name}")

        # 并发处理所有文件（信号量控制并发数）
        import asyncio
        tasks = [
            self.worker_pool.submit(
                self._process_single_file,
                file, knowledge_base, request
            )
            for file in files
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计处理结果
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        failed_count = len(results) - success_count

        logger.info(
            f"文件处理完成，成功: {success_count}, 失败: {failed_count}"
        )

    async def _process_single_file(
        self,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq
    ) -> None:
        """处理单个文件的 ETL 流程

        步骤：
        1. 解析文档（从共享文件系统读取）
        2. 分块
        3. 生成嵌入向量
        4. 存储到 Milvus
        5. 更新文件状态

        Args:
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体
            request: 添加文件请求
        """
        try:
            # 1. 更新状态为处理中
            await self.file_repo.update_status(rag_file.id, FileStatus.PROCESSING)

            # 2. 从 metadata 中获取文件路径和原始文件ID
            file_path = rag_file.file_metadata.get("file_path") if rag_file.file_metadata else None
            original_file_id = rag_file.file_id  # t_dm_dataset_files.id
            dataset_id = rag_file.file_metadata.get("dataset_id") if rag_file.file_metadata else None

            # 2.1 验证文件路径
            if not file_path:
                error_msg = f"文件路径未设置，file_metadata={rag_file.file_metadata}"
                logger.error(error_msg)
                await self.file_repo.update_status(
                    rag_file.id,
                    FileStatus.PROCESS_FAILED,
                    err_msg=error_msg
                )
                return

            # 2.2 确保使用绝对路径
            import os
            file_path = os.path.abspath(file_path)

            # 2.3 验证文件存在
            if not Path(file_path).exists():
                error_msg = f"文件不存在: {file_path}"
                logger.error(error_msg)
                await self.file_repo.update_status(
                    rag_file.id,
                    FileStatus.PROCESS_FAILED,
                    err_msg=error_msg
                )
                return

            # 3. 准备完整的 metadata
            file_extension = Path(file_path).suffix
            base_metadata = {
                "rag_file_id": rag_file.id,
                "original_file_id": original_file_id,
                "dataset_id": dataset_id,
                "file_name": rag_file.file_name,
                "file_extension": file_extension,
                "knowledge_base_id": knowledge_base.id,
                "file_path": file_path,
            }

            # 4. 加载并分块（复用 ingest pipeline），传递完整的 metadata
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
                await self.file_repo.update_status(
                    rag_file.id,
                    FileStatus.PROCESS_FAILED,
                    err_msg=error_msg
                )
                return

            if not chunks:
                logger.warning(f"文件 {rag_file.file_name} 未生成任何分块")
                await self.file_repo.update_status(
                    rag_file.id,
                    FileStatus.PROCESS_FAILED,
                    err_msg="文档解析后未生成任何分块"
                )
                return

            logger.info(f"文件 {rag_file.file_name} 分块完成，共 {len(chunks)} 个分块")

            # 5. 写入 LangChain Milvus 向量存储（自动嵌入 + BM25 全文检索）
            try:
                embedding_entity = await get_model_by_id(self.db, knowledge_base.embedding_model)
                if not embedding_entity:
                    raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

                # 5.1 获取向量维度并创建 Java 兼容的集合
                try:
                    dimension = get_vector_dimension(
                        embedding_model=embedding_entity.model_name,
                        base_url=getattr(embedding_entity, "base_url", None),
                        api_key=getattr(embedding_entity, "api_key", None),
                    )
                    create_java_compatible_collection(
                        collection_name=knowledge_base.name,
                        dimension=dimension
                    )
                except BusinessError as e:
                    logger.warning("创建或检查集合失败: %s", e)
                    # 如果集合已存在，继续处理
                    if "已存在" not in str(e):
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
                    # 确保 metadata 包含所有必需字段
                    for key, value in base_metadata.items():
                        if key not in c.metadata:
                            c.metadata[key] = value
                ids = [str(uuid.uuid4()) for _ in chunks]
                documents, doc_ids = chunks_to_langchain_documents(chunks, ids=ids)
                vectorstore.add_documents(documents=documents, ids=doc_ids)

            except Exception as e:
                error_msg = f"向量化或存储到 Milvus 失败: {str(e)}"
                logger.exception(f"文件 {rag_file.file_name} 向量化失败: {e}")
                await self.file_repo.update_status(
                    rag_file.id,
                    FileStatus.PROCESS_FAILED,
                    err_msg=error_msg
                )
                return

            # 6. 更新文件状态为成功
            await self.file_repo.update_chunk_count(rag_file.id, len(chunks))
            await self.file_repo.update_status(rag_file.id, FileStatus.PROCESSED)

            logger.info(f"文件 {rag_file.file_name} ETL 处理完成")

        except Exception as e:
            logger.exception(f"文件 {rag_file.file_name} 处理失败: {e}")
            await self.file_repo.update_status(
                rag_file.id,
                FileStatus.PROCESS_FAILED,
                err_msg=str(e)
            )
            # 不抛出异常，避免影响其他文件的处理
