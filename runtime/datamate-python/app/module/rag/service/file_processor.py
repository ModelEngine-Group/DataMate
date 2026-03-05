"""
文件处理器

负责文件的后台 ETL 处理：加载、分块、向量化、存储。
支持两种知识库类型：DOCUMENT（向量检索）和 GRAPH（知识图谱）。
使用全局 WorkerPool 实现并发控制，最多 10 个文件并行处理。
支持文本、图片、视频文件的多模态向量化。
"""

import logging
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus, RagType
from app.db.session import AsyncSessionLocal
from app.module.rag.infra.document import ingest_file_to_chunks, DocumentChunk
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.task.worker_pool import get_global_pool
from app.module.rag.infra.vectorstore import VectorStoreFactory, chunks_to_documents
from app.module.rag.repository import RagFileRepository, KnowledgeBaseRepository
from app.module.rag.schema.request import AddFilesReq
from app.module.system.service.common_service import get_model_by_id

logger = logging.getLogger(__name__)

# 支持的图片扩展名（参考 Java 版本 IMAGE_EXTENSIONS）
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff", "tif"}

# 支持的视频扩展名（参考 Java 版本 VIDEO_EXTENSIONS）
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v", "3gp"}


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
        knowledge_base_type: str,
        request_data: dict,
    ) -> None:
        """启动后台文件处理

        Args:
            background_tasks: FastAPI BackgroundTasks
            knowledge_base_id: 知识库 ID
            knowledge_base_name: 知识库名称
            knowledge_base_type: 知识库类型 (DOCUMENT/GRAPH)
            request_data: 添加文件请求数据
        """
        background_tasks.add_task(
            self._process_files_background,
            knowledge_base_id,
            knowledge_base_name,
            knowledge_base_type,
            request_data,
        )
        logger.info("已注册后台任务: 知识库=%s, 类型=%s", knowledge_base_name, knowledge_base_type)

    async def _process_files_background(
        self,
        knowledge_base_id: str,
        knowledge_base_name: str,
        knowledge_base_type: str,
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

                logger.info("开始处理 %d 个文件，知识库: %s, 类型: %s", len(files), knowledge_base_name, knowledge_base_type)

                if knowledge_base_type == RagType.GRAPH.value:
                    await self._process_graph_files(db, files, knowledge_base)
                else:
                    await self._process_document_files(db, files, knowledge_base, request)

                logger.info("知识库 %s 文件处理完成", knowledge_base_name)

            except Exception as e:
                logger.exception("后台处理文件失败: %s", e)
            finally:
                await db.close()

    async def _process_document_files(
        self,
        db: AsyncSession,
        files: List[RagFile],
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        """处理 DOCUMENT 类型文件（向量化）"""
        import asyncio

        async def process_with_semaphore(rag_file: RagFile):
            async with self.worker_pool.semaphore:
                async with AsyncSessionLocal() as file_db:
                    try:
                        await self._process_single_file(
                            file_db, rag_file, knowledge_base, request
                        )
                    finally:
                        await file_db.close()

        tasks = [process_with_semaphore(f) for f in files]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_graph_files(
        self,
        db: AsyncSession,
        files: List[RagFile],
        knowledge_base: KnowledgeBase,
    ) -> None:
        """处理 GRAPH 类型文件（知识图谱）"""
        from app.module.shared.llm import LLMFactory
        from app.module.shared.common.document_loaders import load_documents

        try:
            rag_instance = await self._initialize_graph_rag(db, knowledge_base, LLMFactory)

            for rag_file in files:
                await self._process_single_graph_file(db, rag_file, rag_instance, load_documents)

        except Exception as e:
            logger.exception("初始化知识图谱失败: %s", e)
            for rag_file in files:
                file_repo = RagFileRepository(db)
                await self._mark_failed(db, file_repo, str(rag_file.id), f"知识图谱初始化失败: {str(e)}")  # type: ignore

    async def _initialize_graph_rag(self, db: AsyncSession, knowledge_base: KnowledgeBase, LLMFactory):
        """初始化 GraphRAG 实例"""
        from .graph_rag import (
            DEFAULT_WORKING_DIR,
            build_embedding_func,
            build_llm_model_func,
            initialize_rag,
        )

        embedding_entity = await get_model_by_id(db, str(knowledge_base.embedding_model))  # type: ignore
        if not embedding_entity:
            raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

        chat_entity = await get_model_by_id(db, str(knowledge_base.chat_model))  # type: ignore
        if not chat_entity:
            raise ValueError(f"聊天模型不存在: {knowledge_base.chat_model}")

        llm_callable = await build_llm_model_func(
            str(chat_entity.model_name), str(chat_entity.base_url), str(chat_entity.api_key)  # type: ignore
        )
        embedding_callable = await build_embedding_func(
            str(embedding_entity.model_name),
            str(embedding_entity.base_url),
            str(embedding_entity.api_key),
            embedding_dim=LLMFactory.get_embedding_dimension(
                str(embedding_entity.model_name), str(embedding_entity.base_url), str(embedding_entity.api_key)  # type: ignore
            ),
        )

        kb_working_dir = os.path.join(DEFAULT_WORKING_DIR, str(knowledge_base.name))  # type: ignore
        return await initialize_rag(llm_callable, embedding_callable, kb_working_dir)

    async def _process_single_graph_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        rag_instance,
        load_documents,
    ) -> None:
        """处理单个 GRAPH 类型文件"""
        file_repo = RagFileRepository(db)

        try:
            await self._update_status(db, file_repo, str(rag_file.id), FileStatus.PROCESSING, 10)  # type: ignore
            await db.commit()

            dataset_file = await self._get_dataset_file(db, str(rag_file.file_id))  # type: ignore
            if not dataset_file:
                await self._mark_failed(db, file_repo, str(rag_file.id), "数据集文件不存在")  # type: ignore
                return

            documents = load_documents(str(dataset_file.file_path))  # type: ignore
            if not documents:
                await self._mark_failed(db, file_repo, str(rag_file.id), "文件解析失败，未生成文档")  # type: ignore
                return

            await self._update_progress(db, file_repo, str(rag_file.id), 30)  # type: ignore
            await db.commit()

            for idx, doc in enumerate(documents):
                logger.info("插入文档到知识图谱: %s, 进度: %d/%d", str(rag_file.file_name), idx + 1, len(documents))  # type: ignore
                await rag_instance.ainsert(input=doc.page_content, file_paths=[str(dataset_file.file_path)])  # type: ignore

            await self._mark_success(db, file_repo, str(rag_file.id), len(documents))  # type: ignore
            logger.info("文件 %s 知识图谱处理完成", str(rag_file.file_name))

        except Exception as e:
            logger.exception("文件 %s 知识图谱处理失败: %s", str(rag_file.file_name), e)  # type: ignore
            await self._mark_failed(db, file_repo, str(rag_file.id), str(e))  # type: ignore

    async def _get_dataset_file(self, db: AsyncSession, file_id: str):  # type: ignore
        """获取数据集文件"""
        from sqlalchemy import select
        from app.db.models.dataset_management import DatasetFiles


        result = await db.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        return result.scalar_one_or_none()

    async def _process_single_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        """处理单个文件的 ETL 流程

        1. 验证文件
        2. 检测文件类型（文本/图片/视频）
        3. 根据类型选择处理方式
        4. 向量化并存储
        5. 完成
        """
        file_repo = RagFileRepository(db)

        try:
            # 更新状态为处理中
            await self._update_status(
                db, file_repo, rag_file.id, FileStatus.PROCESSING, 5
            )
            await db.commit()

            # 验证文件并获取路径
            file_path = await self._validate_file(db, file_repo, rag_file)
            if not file_path:
                return

            # 获取文件类型
            file_type = self._get_file_type(rag_file)
            is_image = self._is_image_file(file_type)
            is_video = self._is_video_file(file_type)

            # 获取嵌入模型信息
            embedding_entity = await get_model_by_id(db, knowledge_base.embedding_model)
            if not embedding_entity:
                await self._mark_failed(
                    db,
                    file_repo,
                    rag_file.id,
                    f"嵌入模型不存在: {knowledge_base.embedding_model}",
                )
                return

            is_multimodal = embedding_entity.type == "MULTIMODAL_EMBEDDING"

            # 根据文件类型选择处理方式
            if is_image and is_multimodal:
                await self._process_image_file(
                    db, rag_file, knowledge_base, file_path, file_type
                )
            elif is_video and is_multimodal:
                await self._process_video_file(
                    db, rag_file, knowledge_base, file_path, file_type
                )
            elif is_image:
                await self._mark_failed(
                    db, file_repo, rag_file.id, "图片文件需要多模态嵌入模型支持"
                )
                return
            elif is_video:
                await self._mark_failed(
                    db, file_repo, rag_file.id, "视频文件需要多模态嵌入模型支持"
                )
                return
            else:
                # 文本文件处理
                await self._process_text_file(
                    db, rag_file, knowledge_base, request, file_path
                )

        except Exception as e:
            logger.exception("文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    def _get_file_type(self, rag_file: RagFile) -> str:
        """获取文件类型（扩展名）"""
        file_path = self._get_file_path(rag_file) or ""
        return Path(file_path).suffix.lower().lstrip(".")

    def _is_image_file(self, file_type: str) -> bool:
        """判断是否为图片文件"""
        if not file_type:
            return False
        return file_type.lower() in IMAGE_EXTENSIONS

    def _is_video_file(self, file_type: str) -> bool:
        """判断是否为视频文件"""
        if not file_type:
            return False
        return file_type.lower() in VIDEO_EXTENSIONS

    async def _process_image_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        file_path: str,
        file_type: str,
    ) -> None:
        """处理图片文件（多模态嵌入）

        参考 Java 版本 RagEtlService.processImageFileWithMultimodal 实现
        """
        import asyncio

        file_repo = RagFileRepository(db)

        try:
            # 获取多模态嵌入客户端
            embedding = await self._get_embeddings(db, knowledge_base)

            # 使用多模态嵌入生成向量
            # MultimodalEmbeddingClient.embed_image 方法
            logger.info("正在为图片 %s 生成多模态嵌入向量...", rag_file.file_name)
            embedding_vector = await asyncio.to_thread(
                embedding.embed_image, file_path, ""
            )

            # 创建向量存储
            vectorstore = VectorStoreFactory.create(
                collection_name=knowledge_base.name,
                embedding=embedding,
            )

            # 构建元数据（参考 Java 版本）
            from langchain_core.documents import Document

            doc = Document(
                page_content=f"[图片文件: {rag_file.file_name}]",
                metadata={
                    "rag_file_id": rag_file.id,
                    "original_file_id": rag_file.file_id,
                    "dataset_id": rag_file.file_metadata.get("dataset_id")
                    if rag_file.file_metadata
                    else None,
                    "file_type": file_type,
                    "is_image": "true",  # 关键标记，用于检索时区分
                    "file_name": rag_file.file_name,
                },
            )

            # 存储到 Milvus
            doc_id = str(uuid.uuid4())
            vectorstore.add_documents(documents=[doc], ids=[doc_id])

            # 标记成功
            await self._mark_success(db, file_repo, rag_file.id, 1)
            logger.info("图片文件 %s 多模态向量化完成", rag_file.file_name)

        except Exception as e:
            logger.exception("图片文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    async def _process_video_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        file_path: str,
        file_type: str,
    ) -> None:
        """处理视频文件（多模态嵌入）

        参考 Java 版本 RagEtlService.processVideoFileWithMultimodal 实现
        """
        import asyncio

        file_repo = RagFileRepository(db)

        try:
            # 获取多模态嵌入客户端
            embedding = await self._get_embeddings(db, knowledge_base)

            # 使用多模态嵌入生成向量
            logger.info("正在为视频 %s 生成多模态嵌入向量...", rag_file.file_name)
            embedding_vector = await asyncio.to_thread(
                embedding.embed_video, file_path, ""
            )

            # 创建向量存储
            vectorstore = VectorStoreFactory.create(
                collection_name=knowledge_base.name,
                embedding=embedding,
            )

            # 构建元数据（参考 Java 版本）
            from langchain_core.documents import Document

            doc = Document(
                page_content=f"[视频文件: {rag_file.file_name}]",
                metadata={
                    "rag_file_id": rag_file.id,
                    "original_file_id": rag_file.file_id,
                    "dataset_id": rag_file.file_metadata.get("dataset_id")
                    if rag_file.file_metadata
                    else None,
                    "file_type": file_type,
                    "is_video": "true",  # 关键标记，用于检索时区分
                    "file_name": rag_file.file_name,
                },
            )

            # 存储到 Milvus
            doc_id = str(uuid.uuid4())
            vectorstore.add_documents(documents=[doc], ids=[doc_id])

            # 标记成功
            await self._mark_success(db, file_repo, rag_file.id, 1)
            logger.info("视频文件 %s 多模态向量化完成", rag_file.file_name)

        except Exception as e:
            logger.exception("视频文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    async def _process_text_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
        file_path: str,
    ) -> None:
        """处理文本文件（原有逻辑）

        1. 加载并分块
        2. 向量化并存储
        """
        file_repo = RagFileRepository(db)

        # 加载并分块文档
        metadata = self._build_chunk_metadata(rag_file, knowledge_base)
        chunks = await self._load_and_split(file_path, rag_file, metadata, request)

        if not chunks:
            await self._mark_failed(
                db, file_repo, rag_file.id, "文档解析后未生成任何分块"
            )
            return

        logger.info("文件 %s 分块完成，共 %d 个分块", rag_file.file_name, len(chunks))

        # 向量化并存储到 Milvus
        await self._embed_and_store(db, chunks, rag_file, knowledge_base)

        # 标记完成
        await self._mark_success(db, file_repo, rag_file.id, len(chunks))
        logger.info("文件 %s ETL 处理完成", rag_file.file_name)

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
            await self._mark_failed(
                db, file_repo, rag_file.id, f"文件不存在: {file_path}"
            )
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
            logger.info(
                "文件 %s 加载分块成功，数量: %d", rag_file.file_name, len(chunks)
            )

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
        vectorstore = await self._create_vectorstore(
            db, knowledge_base, file_repo, rag_file
        )

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
                    len(chunk.text) if chunk.text else 0,
                )

        if not valid_chunks:
            logger.warning("文件 %s 没有有效的分块内容", rag_file.file_name)
            return []

        logger.info(
            "文件 %s 有效分块数量: %d / %d",
            rag_file.file_name,
            len(valid_chunks),
            len(chunks),
        )
        return valid_chunks

    def _log_chunk_cleaning(
        self, idx: int, original_text: str, cleaned_text: str
    ) -> None:
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
            "..." if original_text and len(original_text) > 100 else "",
        )
        logger.debug(
            "分块 %d 清理后 (长度=%d): %.100s%s",
            idx,
            len(cleaned_text) if cleaned_text else 0,
            repr(cleaned_text[:100]) if cleaned_text else "None",
            "..." if cleaned_text and len(cleaned_text) > 100 else "",
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
                vectorstore, batch_chunks, batch_start, batch_end, total_chunks
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
                documents[0].page_content if documents else "N/A",
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
                "..." if len(chunk.text) > 50 else "",
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
            model_type=embedding_entity.type,
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

    def _build_chunk_metadata(
        self, rag_file: RagFile, knowledge_base: KnowledgeBase
    ) -> dict:
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
            "dataset_id": rag_file.file_metadata.get("dataset_id")
            if rag_file.file_metadata
            else None,
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

        text = re.sub(r"[\x00-\x09\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        text = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        import re

        text = re.sub(r"[ \t]+", " ", text)
        text = "\n".join(line.strip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _remove_empty_lines(self, text: str) -> str:
        """移除空行

        Args:
            text: 原始文本

        Returns:
            移除空行后的文本
        """
        return "\n".join(line for line in text.split("\n") if line.strip())

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
        return bool(re.search(r"[\w\u4e00-\u9fff]", text))

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
        await file_repo.update_status(
            rag_file_id, FileStatus.PROCESS_FAILED, err_msg=err_msg
        )
        await db.commit()
