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
                async with AsyncSessionLocal() as file_db:
                    try:
                        await self._process_single_file(file_db, rag_file, knowledge_base, request)
                    finally:
                        await file_db.close()

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

        # 过滤和清理分块
        valid_chunks = await self._filter_and_clean_chunks(chunks, rag_file)
        if not valid_chunks:
            return

        # 创建向量存储
        vectorstore = await self._create_vectorstore(db, knowledge_base, file_repo, rag_file)

        # 添加元数据
        self._add_metadata_to_chunks(valid_chunks, rag_file, knowledge_base)

        # 分批存储
        await self._store_chunks_in_batches(vectorstore, valid_chunks, rag_file)

    async def _filter_and_clean_chunks(
        self,
        chunks: List[DocumentChunk],
        rag_file: RagFile,
    ) -> List[DocumentChunk]:
        """过滤和清理无效的分块

        Args:
            chunks: 原始分块列表
            rag_file: RAG 文件实体

        Returns:
            有效的分块列表
        """
        valid_chunks = []
        for idx, chunk in enumerate(chunks):
            cleaned_text = self._clean_text(chunk.text)
            self._log_chunk_cleaning(idx, chunk.text, cleaned_text)

            if cleaned_text and len(cleaned_text.strip()) > 0:
                chunk.text = cleaned_text
                valid_chunks.append(chunk)
            else:
                logger.warning(
                    "跳过无效分块: rag_file_id=%s, chunk_index=%s, 原始长度=%d",
                    rag_file.id,
                    chunk.metadata.get("chunk_index"),
                    len(chunk.text) if chunk.text else 0
                )

        if not valid_chunks:
            logger.warning("文件 %s 没有有效的分块内容", rag_file.file_name)
            return []

        logger.info(
            "文件 %s 有效分块数量: %d / %d",
            rag_file.file_name,
            len(valid_chunks),
            len(chunks)
        )
        return valid_chunks

    def _log_chunk_cleaning(self, idx: int, original_text: str, cleaned_text: str) -> None:
        """记录分块清理日志

        Args:
            idx: 分块索引
            original_text: 原始文本
            cleaned_text: 清理后文本
        """
        if idx >= 3:
            return

        logger.debug(
            "分块 %d 清理前 (长度=%d): %.100s%s",
            idx,
            len(original_text) if original_text else 0,
            repr(original_text[:100]) if original_text else "None",
            "..." if original_text and len(original_text) > 100 else ""
        )
        logger.debug(
            "分块 %d 清理后 (长度=%d): %.100s%s",
            idx,
            len(cleaned_text) if cleaned_text else 0,
            repr(cleaned_text[:100]) if cleaned_text else "None",
            "..." if cleaned_text and len(cleaned_text) > 100 else ""
        )

    async def _create_vectorstore(
        self,
        db: AsyncSession,
        knowledge_base: KnowledgeBase,
        file_repo: RagFileRepository,
        rag_file: RagFile,
    ):
        """创建向量存储

        Args:
            db: 数据库 session
            knowledge_base: 知识库实体
            file_repo: 文件仓储
            rag_file: RAG 文件实体

        Returns:
            向量存储实例
        """
        embedding = await self._get_embeddings(db, knowledge_base)
        vectorstore = VectorStoreFactory.create(
            collection_name=knowledge_base.name,
            embedding=embedding,
        )

        await self._update_progress(db, file_repo, rag_file.id, 60)
        await db.commit()

        return vectorstore

    def _add_metadata_to_chunks(
        self,
        chunks: List[DocumentChunk],
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
    ) -> None:
        """为分块添加元数据

        Args:
            chunks: 分块列表
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体
        """
        base_metadata = {
            "rag_file_id": rag_file.id,
            "original_file_id": rag_file.file_id,
            "knowledge_base_id": knowledge_base.id,
        }

        for chunk in chunks:
            chunk.metadata.update(base_metadata)

    async def _store_chunks_in_batches(
        self,
        vectorstore,
        chunks: List[DocumentChunk],
        rag_file: RagFile,
    ) -> None:
        """分批存储分块到向量数据库

        Args:
            vectorstore: 向量存储实例
            chunks: 分块列表
            rag_file: RAG 文件实体
        """
        batch_size = 20
        total_chunks = len(chunks)

        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = chunks[batch_start:batch_end]

            await self._store_single_batch(
                vectorstore,
                batch_chunks,
                batch_start,
                batch_end,
                total_chunks
            )

        logger.info("文件 %s 向量存储完成，数量: %d", rag_file.file_name, len(chunks))

    async def _store_single_batch(
        self,
        vectorstore,
        batch_chunks: List[DocumentChunk],
        batch_start: int,
        batch_end: int,
        total_chunks: int,
    ) -> None:
        """存储单个批次的分块

        Args:
            vectorstore: 向量存储实例
            batch_chunks: 批次分块列表
            batch_start: 批次起始索引
            batch_end: 批次结束索引
            total_chunks: 总分块数
        """
        logger.info("处理分块批次 %d-%d / %d", batch_start + 1, batch_end, total_chunks)

        self._log_batch_details(batch_chunks, batch_start)

        ids = [str(uuid.uuid4()) for _ in batch_chunks]
        documents, doc_ids = chunks_to_documents(batch_chunks, ids=ids)

        try:
            vectorstore.add_documents(documents=documents, ids=doc_ids)
            logger.info("批次 %d-%d 存储成功", batch_start + 1, batch_end)
        except Exception as e:
            logger.error(
                "批次 %d-%d 存储失败: %s\n第一个文档内容: %.200s",
                batch_start + 1,
                batch_end,
                str(e),
                documents[0].page_content if documents else "N/A"
            )
            raise

    def _log_batch_details(
        self,
        batch_chunks: List[DocumentChunk],
        batch_start: int,
    ) -> None:
        """记录批次详细信息

        Args:
            batch_chunks: 批次分块列表
            batch_start: 批次起始索引
        """
        for i, chunk in enumerate(batch_chunks[:2]):
            logger.debug(
                "批次内分块 %d: 长度=%d, 文本=%.50s%s",
                batch_start + i,
                len(chunk.text),
                chunk.text[:50],
                "..." if len(chunk.text) > 50 else ""
            )

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

    def _clean_text(self, text: str) -> str:
        """清理文本内容

        移除无效字符、控制字符，并规范化空白字符。

        Args:
            text: 原始文本

        Returns:
            清理后的文本，如果无效则返回空字符串
        """
        import re

        if not text or not isinstance(text, str):
            return ""

        text = self._remove_control_characters(text)
        text = self._normalize_whitespace(text)
        text = self._remove_empty_lines(text)

        if not self._has_printable_content(text):
            return ""

        return text.strip()

    def _remove_control_characters(self, text: str) -> str:
        """移除控制字符和零宽字符

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        import re
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[\u200b-\u200f\u2028-\u202f\ufeff]', '', text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        import re
        text = re.sub(r'[ \t]+', ' ', text)
        text = '\n'.join(line.strip() for line in text.split('\n'))
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def _remove_empty_lines(self, text: str) -> str:
        """移除空行

        Args:
            text: 原始文本

        Returns:
            移除空行后的文本
        """
        return '\n'.join(line for line in text.split('\n') if line.strip())

    def _has_printable_content(self, text: str) -> bool:
        """检查文本是否包含可打印内容

        Args:
            text: 文本内容

        Returns:
            是否包含可打印字符
        """
        import re
        if not text or not text.strip():
            return False
        return bool(re.search(r'[\w\u4e00-\u9fff]', text))

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
