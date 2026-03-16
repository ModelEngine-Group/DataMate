"""
文件处理器

负责文件的后台 ETL 处理：加载、分块、向量化、存储。
支持两种知识库类型：DOCUMENT（向量检索）和 GRAPH（知识图谱）。
使用全局 WorkerPool 实现并发控制，最多 10 个文件并行处理。
"""
import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus, RagType
from app.db.session import AsyncSessionLocal
from app.module.rag.infra.document import ingest_file_to_chunks
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.task.worker_pool import get_global_pool
from app.module.rag.infra.vectorstore import VectorStoreFactory
from app.module.rag.repository import RagFileRepository, KnowledgeBaseRepository
from app.module.rag.schema.request import AddFilesReq
from app.module.rag.service.common import (
    TextCleaner,
    MetadataBuilder,
    BatchProcessor,
    get_file_path,
)
from app.module.system.service.common_service import get_model_by_id

logger = logging.getLogger(__name__)


class FileProcessor:

    def __init__(self):
        self.worker_pool = get_global_pool(max_workers=10)

    def start_background_processing(
        self,
        background_tasks: BackgroundTasks,
        knowledge_base_id: str,
        knowledge_base_name: str,
        knowledge_base_type: str,
        request_data: dict,
    ) -> None:
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
                    await self._process_document_files(files, knowledge_base, request)

                logger.info("知识库 %s 文件处理完成", knowledge_base_name)

            except Exception as e:
                logger.exception("后台处理文件失败: %s", e)
            finally:
                await db.close()

    async def _process_document_files(
        self,
        files: List[RagFile],
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        async def process_with_semaphore(rag_file: RagFile):
            async with self.worker_pool.semaphore:
                async with AsyncSessionLocal() as file_db:
                    try:
                        await self._process_single_file(file_db, rag_file, knowledge_base, request)
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
        from app.module.shared.common.document_loaders import load_documents

        try:
            rag_instance = await self._initialize_graph_rag(db, knowledge_base)

            for rag_file in files:
                await self._process_single_graph_file(db, rag_file, rag_instance, load_documents)

        except Exception as e:
            logger.exception("初始化知识图谱失败: %s", e)
            for rag_file in files:
                file_repo = RagFileRepository(db)
                await self._mark_failed(db, file_repo, str(rag_file.id), f"知识图谱初始化失败: {str(e)}")

    @staticmethod
    async def _initialize_graph_rag(db: AsyncSession, knowledge_base: KnowledgeBase):
        from app.module.rag.service.strategy.graph_strategy import GraphKnowledgeBaseStrategy
        strategy = GraphKnowledgeBaseStrategy(db)
        return await strategy._get_or_create_graph_rag(knowledge_base)

    async def _process_single_graph_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        rag_instance,
        load_documents,
    ) -> None:
        file_repo = RagFileRepository(db)

        try:
            await self._update_status(db, file_repo, str(rag_file.id), FileStatus.PROCESSING, 10)
            await db.commit()

            file_path = get_file_path(rag_file)
            if not file_path or not Path(file_path).exists():
                await self._mark_failed(db, file_repo, str(rag_file.id), "文件不存在")
                return

            documents = await asyncio.to_thread(load_documents, file_path)
            if not documents:
                await self._mark_failed(db, file_repo, str(rag_file.id), "文件解析失败，未生成文档")
                return

            await self._update_progress(db, file_repo, str(rag_file.id), 30)
            await db.commit()

            all_content = "\n\n".join(doc.page_content for doc in documents)
            doc_id = str(rag_file.id)
            logger.info("插入文档到知识图谱: %s, doc_id=%s, 文档数=%d", str(rag_file.file_name), doc_id, len(documents))
            await rag_instance.ainsert(input=all_content, file_paths=[file_path], ids=doc_id)

            doc_status_data = await rag_instance.doc_status.get_by_id(doc_id)
            chunk_count = len(doc_status_data.get("chunks_list", [])) if doc_status_data else 0
            await self._mark_success(db, file_repo, str(rag_file.id), chunk_count)
            logger.info("文件 %s 知识图谱处理完成, 实际分块数: %d", str(rag_file.file_name), chunk_count)

        except Exception as e:
            logger.exception("文件 %s 知识图谱处理失败: %s", str(rag_file.file_name), e)
            await self._mark_failed(db, file_repo, str(rag_file.id), str(e))

    async def _process_single_file(
        self,
        db: AsyncSession,
        rag_file: RagFile,
        knowledge_base: KnowledgeBase,
        request: AddFilesReq,
    ) -> None:
        file_repo = RagFileRepository(db)

        try:
            await self._update_status(db, file_repo, rag_file.id, FileStatus.PROCESSING, 5)
            await db.commit()

            file_path = get_file_path(rag_file)
            if not file_path or not Path(file_path).exists():
                await self._mark_failed(db, file_repo, rag_file.id, "文件不存在")
                return

            base_metadata = MetadataBuilder.build_chunk_metadata(rag_file, knowledge_base)
            chunks = await ingest_file_to_chunks(
                file_path,
                process_type=request.process_type,
                chunk_size=request.chunk_size,
                overlap_size=request.overlap_size,
                delimiter=request.delimiter,
                **base_metadata,
            )

            if not chunks:
                await self._mark_failed(db, file_repo, rag_file.id, "文档解析后未生成任何分块")
                return

            logger.info("文件 %s 分块完成，共 %d 个分块", rag_file.file_name, len(chunks))

            valid_chunks = self._filter_and_clean_chunks(chunks, rag_file)
            if not valid_chunks:
                await self._mark_failed(db, file_repo, rag_file.id, "文件没有有效的分块内容")
                return

            embedding = await self._get_embeddings(db, knowledge_base)
            vectorstore = VectorStoreFactory.create(
                collection_name=str(knowledge_base.name),
                embedding=embedding,
            )

            await self._update_progress(db, file_repo, rag_file.id, 60)
            await db.commit()

            MetadataBuilder.add_to_chunks(valid_chunks, {
                "rag_file_id": str(rag_file.id),
                "original_file_id": str(rag_file.file_id),
                "knowledge_base_id": str(knowledge_base.id),
            })

            await BatchProcessor.store_in_batches(vectorstore, valid_chunks)

            await self._mark_success(db, file_repo, rag_file.id, len(valid_chunks))
            logger.info("文件 %s ETL 处理完成", rag_file.file_name)

        except Exception as e:
            logger.exception("文件 %s 处理失败: %s", rag_file.file_name, e)
            await self._mark_failed(db, file_repo, rag_file.id, str(e))

    @staticmethod
    def _filter_and_clean_chunks(chunks: list, rag_file: RagFile) -> list:
        valid_chunks = []
        for chunk in chunks:
            cleaned_text = TextCleaner.clean(chunk.text)

            if cleaned_text and TextCleaner.has_printable_content(cleaned_text):
                chunk.text = cleaned_text
                valid_chunks.append(chunk)
            else:
                logger.warning(
                    "跳过无效分块: rag_file_id=%s, chunk_index=%s",
                    rag_file.id,
                    chunk.metadata.get("chunk_index")
                )

        logger.info("文件 %s 有效分块数量: %d / %d", rag_file.file_name, len(valid_chunks), len(chunks))
        return valid_chunks

    @staticmethod
    async def _get_embeddings(db: AsyncSession, knowledge_base: KnowledgeBase):
        embedding_entity = await get_model_by_id(db, str(knowledge_base.embedding_model))
        if not embedding_entity:
            raise ValueError(f"嵌入模型不存在: {knowledge_base.embedding_model}")

        return EmbeddingFactory.create_embeddings(
            model_name=str(embedding_entity.model_name),
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

    @staticmethod
    async def _update_status(
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        status: FileStatus,
        progress: int = 0,
    ) -> None:
        await file_repo.update_status(rag_file_id, status)
        await file_repo.update_progress(rag_file_id, progress)
        await db.flush()

    @staticmethod
    async def _update_progress(
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        progress: int,
    ) -> None:
        await file_repo.update_progress(rag_file_id, progress)
        await db.flush()

    @staticmethod
    async def _mark_success(
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        chunk_count: int,
    ) -> None:
        await file_repo.update_chunk_count(rag_file_id, chunk_count)
        await file_repo.update_status(rag_file_id, FileStatus.PROCESSED)
        await file_repo.update_progress(rag_file_id, 100)
        await db.commit()

    @staticmethod
    async def _mark_failed(
        db: AsyncSession,
        file_repo: RagFileRepository,
        rag_file_id: str,
        err_msg: str,
    ) -> None:
        logger.error("文件处理失败: %s", err_msg)
        await file_repo.update_status(rag_file_id, FileStatus.PROCESS_FAILED, err_msg=err_msg)
        await db.commit()
