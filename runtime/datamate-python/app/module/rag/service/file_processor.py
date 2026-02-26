"""
文件处理器

负责文件的后台 ETL 处理：加载、分块、向量化、存储。
使用全局 WorkerPool 实现并发控制，最多 10 个文件并行处理。
"""
import logging
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus
from app.db.session import AsyncSessionLocal
from app.module.rag.infra.document import ingest_file_to_chunks, DocumentChunk
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.task.worker_pool import get_global_pool
from app.module.rag.infra.vectorstore import VectorStoreFactory, chunks_to_documents
from app.module.rag.repository import RagFileRepository, KnowledgeBaseRepository
from app.module.rag.schema.request import AddFilesReq
from app.module.system.service.common_service import get_model_by_id

logger = logging.getLogger(__name__)


class FileProcessor:
    """文件处理器

    负责文件的后台 ETL 处理，使用全局 WorkerPool 控制并发。
    """

    def __init__(self):
        """初始化处理器"""
        self.worker_pool = get_global_pool(max_workers=10)

    def start_background_processing(
        self,
        background_tasks: BackgroundTasks,
        knowledge_base_id: str,
        knowledge_base_name: str,
        request_data: dict,
    ) -> None:
        """启动后台文件处理

        Args:
            background_tasks: FastAPI BackgroundTasks
            knowledge_base_id: 知识库 ID
            knowledge_base_name: 知识库名称
            request_data: 添加文件请求数据
        """
        background_tasks.add_task(
            self._process_files_background,
            knowledge_base_id,
            knowledge_base_name,
            request_data,
        )
        logger.info("已注册后台任务: 知识库=%s", knowledge_base_name)

    async def _process_files_background(
        self,
        knowledge_base_id: str,
        knowledge_base_name: str,
        request_data: dict,
    ) -> None:
        """后台处理文件（使用新的数据库 session）"""
        async with AsyncSessionLocal() as db:
            try:
                kb_repo = KnowledgeBaseRepository(db)
                file_repo = RagFileRepository(db)

                knowledge_base = await kb_repo.get_by_id(knowledge_base_id)
                if not knowledge_base:
                    logger.error("知识库不存在: %s", knowledge_base_id)
                    return

                request = AddFilesReq.model_validate(request_data)
                files = await file_repo.get_unprocessed_files(knowledge_base_id)

                if not files:
                    logger.info("知识库 %s 没有待处理的文件", knowledge_base_name)
                    return

                logger.info("开始处理 %d 个文件，知识库: %s", len(files), knowledge_base_name)

                # 并发处理文件
                await self._process_files_concurrently(db, files, knowledge_base, request)

                logger.info("知识库 %s 文件处理完成", knowledge_base_name)

            except Exception as e:
                logger.exception("后台处理文件失败: %s", e)
            finally:
                await db.close()

    async def _process_files_concurrently(
        self,
        db: AsyncSession,
        files: List[RagFile],
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        """并发处理多个文件（最多10个并行）"""
        import asyncio

        async def process_with_semaphore(rag_file: RagFile):
            async with self.worker_pool.semaphore:
                await self._process_single_file(db, rag_file, knowledge_base, request)

        tasks = [process_with_semaphore(f) for f in files]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_single_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        """处理单个文件的 ETL 流程"""
        file_repo = RagFileRepository(db)

        try:
            # 1. 更新状态为处理中
            await file_repo.update_status(rag_file.id, FileStatus.PROCESSING)
            await db.commit()

            # 2. 验证文件
            file_path = self._get_file_path(rag_file)
            if not file_path:
                await self._mark_failed(db, file_repo, rag_file.id, "文件路径未设置")
                return

            if not Path(file_path).exists():
                await self._mark_failed(db, file_repo, rag_file.id, f"文件不存在: {file_path}")
                return

            # 3. 加载并分块
            metadata = self._build_chunk_metadata(rag_file, knowledge_base)
            chunks = await ingest_file_to_chunks(
                file_path,
                process_type=request.process_type,
                chunk_size=request.chunk_size,
                overlap_size=request.overlap_size,
                delimiter=request.delimiter,
                **metadata,
            )

            if not chunks:
                await self._mark_failed(db, file_repo, rag_file.id, "文档解析后未生成任何分块")
                return

            logger.info("文件 %s 分块完成，共 %d 个分块", rag_file.file_name, len(chunks))

            # 4. 向量化并存储
            await self._embed_and_store(db, chunks, metadata, knowledge_base)

            # 5. 更新文件状态为成功
            await file_repo.update_chunk_count(rag_file.id, len(chunks))
            await file_repo.update_status(rag_file.id, FileStatus.PROCESSED)
            await db.commit()

            logger.info("文件 %s ETL 处理完成", rag_file.file_name)

        except Exception as e:
            logger.exception("文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    def _get_file_path(self, rag_file: RagFile) -> str | None:
        """获取文件绝对路径"""
        if not rag_file.file_metadata:
            return None

        file_path = rag_file.file_metadata.get("file_path")
        if file_path:
            return os.path.abspath(file_path)
        return None

    def _build_chunk_metadata(self, rag_file: RagFile, knowledge_base: KnowledgeBase) -> dict:
        """构建分块元数据"""
        file_path = self._get_file_path(rag_file) or ""
        return {
            "rag_file_id": rag_file.id,
            "original_file_id": rag_file.file_id,
            "dataset_id": rag_file.file_metadata.get("dataset_id") if rag_file.file_metadata else None,
            "file_name": rag_file.file_name,
            "file_extension": Path(file_path).suffix,
            "knowledge_base_id": knowledge_base.id,
        }

    async def _embed_and_store(
        self,
        db: AsyncSession,
        chunks: List[DocumentChunk],
        metadata: dict,
        knowledge_base: KnowledgeBase,
    ) -> None:
        """向量化并存储到 Milvus"""
        embedding_entity = await get_model_by_id(db, knowledge_base.embedding_model)
        if not embedding_entity:
            raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

        embedding = EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

        vectorstore = VectorStoreFactory.create(
            collection_name=knowledge_base.name,
            embedding=embedding,
        )

        # 补充 metadata
        for chunk in chunks:
            for key, value in metadata.items():
                if key not in chunk.metadata:
                    chunk.metadata[key] = value

        ids = [str(uuid.uuid4()) for _ in chunks]
        documents, doc_ids = chunks_to_documents(chunks, ids=ids)
        vectorstore.add_documents(documents=documents, ids=doc_ids)

    async def _mark_failed(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        err_msg: str,
    ) -> None:
        """标记文件处理失败"""
        logger.error("文件处理失败: %s", err_msg)
        await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED, err_msg=err_msg)
        await db.commit()
