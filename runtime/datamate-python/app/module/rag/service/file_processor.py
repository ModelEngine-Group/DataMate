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

                # 并发处理文件（最多 10 个并行）
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
        """处理单个文件的 ETL 流程

        1. 验证文件
        2. 加载并分块（progress=20%）
        3. 向量化并存储（progress=60%）
        4. 完成（progress=100%）
        """
        file_repo = RagFileRepository(db)

        try:
            # 更新状态为处理中
            await self._update_status(db, file_repo, rag_file.id, FileStatus.PROCESSING, 5)
            await db.commit()

            # 验证文件并获取路径
            file_path = await self._validate_file(db, file_repo, rag_file)
            if not file_path:
                return

            # 加载并分块文档
            metadata = self._build_chunk_metadata(rag_file, knowledge_base)
            chunks = await self._load_and_split(file_path, rag_file, metadata, request)

            if not chunks:
                await self._mark_failed(db, file_repo, rag_file.id, "文档解析后未生成任何分块")
                return

            logger.info("文件 %s 分块完成，共 %d 个分块", rag_file.file_name, len(chunks))

            # 向量化并存储到 Milvus
            await self._embed_and_store(db, chunks, rag_file, knowledge_base)

            # 标记完成
            await self._mark_success(db, file_repo, rag_file.id, len(chunks))
            logger.info("文件 %s ETL 处理完成", rag_file.file_name)

        except Exception as e:
            logger.exception("文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    async def _validate_file(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file: RagFile,
    ) -> str | None:
        """验证文件路径并返回绝对路径

        Args:
            db: 数据库 session
            file_repo: 文件仓储
            rag_file: RAG 文件实体

        Returns:
            文件绝对路径，验证失败返回 None
        """
        file_path = self._get_file_path(rag_file)

        if not file_path:
            await self._mark_failed(db, file_repo, rag_file.id, "文件路径未设置")
            return None

        if not Path(file_path).exists():
            await self._mark_failed(db, file_repo, rag_file.id, f"文件不存在: {file_path}")
            return None

        return file_path

    async def _load_and_split(
        self,
        file_path: str,
        rag_file: RagFile,
        metadata: dict,
        request: AddFilesReq,
    ) -> List[DocumentChunk]:
        """加载文档并分块

        Args:
            file_path: 文件路径
            rag_file: RAG 文件实体
            metadata: 基础元数据
            request: 添加文件请求

        Returns:
            文档分块列表
        """
        chunks = await ingest_file_to_chunks(
            file_path,
            process_type=request.process_type,
            chunk_size=request.chunk_size,
            overlap_size=request.overlap_size,
            delimiter=request.delimiter,
            **metadata,
        )

        if chunks:
            logger.info("文件 %s 加载分块成功，数量: %d", rag_file.file_name, len(chunks))

        return chunks

    async def _embed_and_store(
        self,
        db: AsyncSession,
        chunks: List[DocumentChunk],
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
    ) -> None:
        """向量化并存储到 Milvus

        Args:
            db: 数据库 session
            chunks: 文档分块列表
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体
        """
        file_repo = RagFileRepository(db)

        # 获取或创建 Embeddings 实例
        embedding = await self._get_embeddings(db, knowledge_base)

        # 创建向量存储
        vectorstore = VectorStoreFactory.create(
            collection_name=knowledge_base.name,
            embedding=embedding,
        )

        # 更新进度
        await self._update_progress(db, file_repo, rag_file.id, 60)
        await db.commit()

        # 构建完整的 metadata
        base_metadata = {
            "rag_file_id": rag_file.id,
            "original_file_id": rag_file.file_id,
            "knowledge_base_id": knowledge_base.id,
        }

        for chunk in chunks:
            chunk.metadata.update(base_metadata)

        # 生成 ID 并存储
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents, doc_ids = chunks_to_documents(chunks, ids=ids)
        vectorstore.add_documents(documents=documents, ids=doc_ids)

        logger.info("文件 %s 向量存储完成，数量: %d", rag_file.file_name, len(chunks))

    async def _get_embeddings(
        self,
        db: AsyncSession,
        knowledge_base: KnowledgeBase,
    ):
        """获取嵌入模型实例

        Args:
            db: 数据库 session
            knowledge_base: 知识库实体

        Returns:
            LangChain Embeddings 实例
        """
        embedding_entity = await get_model_by_id(db, knowledge_base.embedding_model)
        if not embedding_entity:
            raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

        return EmbeddingFactory.create_embeddings(
            model_name=embedding_entity.model_name,
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

    def _get_file_path(self, rag_file: RagFile) -> str | None:
        """获取文件绝对路径

        Args:
            rag_file: RAG 文件实体

        Returns:
            文件绝对路径，不存在返回 None
        """
        if not rag_file.file_metadata:
            return None

        file_path = rag_file.file_metadata.get("file_path")
        if file_path:
            return os.path.abspath(file_path)
        return None

    def _build_chunk_metadata(self, rag_file: RagFile, knowledge_base: KnowledgeBase) -> dict:
        """构建分块基础元数据

        Args:
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体

        Returns:
            元数据字典
        """
        file_path = self._get_file_path(rag_file) or ""
        return {
            "rag_file_id": rag_file.id,
            "original_file_id": rag_file.file_id,
            "dataset_id": rag_file.file_metadata.get("dataset_id") if rag_file.file_metadata else None,
            "file_name": rag_file.file_name,
            "file_extension": Path(file_path).suffix,
            "knowledge_base_id": knowledge_base.id,
        }

    async def _update_status(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        status: FileStatus,
        progress: int = 0,
    ) -> None:
        """更新文件状态和进度

        Args:
            db: 数据库 session
            file_repo: 文件仓储
            rag_file_id: RAG 文件 ID
            status: 新状态
            progress: 新进度
        """
        await file_repo.update_status(rag_file_id, status)
        await file_repo.update_progress(rag_file_id, progress)
        await db.flush()

    async def _update_progress(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        progress: int,
    ) -> None:
        """更新文件处理进度

        Args:
            db: 数据库 session
            file_repo: 文件仓储
            rag_file_id: RAG 文件 ID
            progress: 进度值 (0-100)
        """
        await file_repo.update_progress(rag_file_id, progress)
        await db.flush()

    async def _mark_success(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        chunk_count: int,
    ) -> None:
        """标记文件处理成功

        Args:
            db: 数据库 session
            file_repo: 文件仓储
            rag_file_id: RAG 文件 ID
            chunk_count: 分块数量
        """
        await file_repo.update_chunk_count(rag_file_id, chunk_count)
        await file_repo.update_status(rag_file_id, FileStatus.PROCESSED)
        await file_repo.update_progress(rag_file_id, 100)
        await db.commit()

    async def _mark_failed(
        self,
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        err_msg: str,
    ) -> None:
        """标记文件处理失败

        Args:
            db: 数据库 session
            file_repo: 文件仓储
            rag_file_id: RAG 文件 ID
            err_msg: 错误信息
        """
        logger.error("文件处理失败: %s", err_msg)
        await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED, err_msg=err_msg)
        await db.commit()
