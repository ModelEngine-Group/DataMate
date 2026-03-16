"""
知识库业务服务

实现知识库的 CRUD 操作和文件管理。
对应 Java: com.datamate.rag.indexer.application.KnowledgeBaseService
"""
import logging
import uuid
from typing import List, Tuple, Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.db.models.dataset_management import DatasetFiles
from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus, RagType
from app.db.models.models import Models
from app.module.rag.infra.embeddings import EmbeddingFactory
from app.module.rag.infra.vectorstore import (
    drop_collection,
    rename_collection,
    delete_chunks_by_rag_file_ids,
    update_chunk_by_id,
    delete_chunk_by_id,
)
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.request import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseUpdateReq,
    KnowledgeBaseQueryReq,
    AddFilesReq,
    DeleteFilesReq,
    RagFileReq,
)
from app.module.rag.schema.response import KnowledgeBaseResp, PagedResponse, RagFileResp, ModelConfig
from app.module.rag.service.file_processor import FileProcessor

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库业务服务类

    功能：
    1. 知识库 CRUD 操作
    2. 文件管理（添加、删除、查询）
    """

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.file_repo = RagFileRepository(db)
        self.file_processor = FileProcessor()

    # ==================== 知识库 CRUD ====================

    async def create(self, request: KnowledgeBaseCreateReq) -> str:
        """创建知识库

        Args:
            request: 创建请求

        Returns:
            知识库 ID
        """
        knowledge_base = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            type=request.type,
            embedding_model=request.embedding_model,
            chat_model=request.chat_model,
        )

        knowledge_base = await self.kb_repo.create(knowledge_base)
        await self.db.commit()

        logger.info("成功创建知识库: %s", request.name)
        return knowledge_base.id

    async def update(self, knowledge_base_id: str, request: KnowledgeBaseUpdateReq) -> None:
        """更新知识库

        Args:
            knowledge_base_id: 知识库 ID
            request: 更新请求
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        old_name = str(knowledge_base.name)
        new_name = request.name
        kb_type = knowledge_base.type

        if new_name and new_name != old_name:
            if await self.kb_repo.exists_by_name(new_name, exclude_id=knowledge_base_id):
                raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_ALREADY_EXISTS, data={"name": new_name})

        knowledge_base.name = request.name
        knowledge_base.description = request.description

        await self.kb_repo.update(knowledge_base)

        if old_name != new_name:
            try:
                if kb_type == RagType.DOCUMENT.value:
                    rename_collection(old_name, new_name)
                elif kb_type == RagType.GRAPH.value:
                    from app.module.rag.service.strategy.graph_strategy import GraphKnowledgeBaseStrategy
                    GraphKnowledgeBaseStrategy.rename_workspace(old_name, new_name)
                    GraphKnowledgeBaseStrategy.clear_cache(old_name)
            except BusinessError:
                await self.db.rollback()
                raise

        await self.db.commit()

    async def delete(self, knowledge_base_id: str) -> None:
        """删除知识库

        Args:
            knowledge_base_id: 知识库 ID
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        kb_name = str(knowledge_base.name)
        kb_type = knowledge_base.type

        await self.file_repo.delete_by_knowledge_base(knowledge_base_id)
        await self.kb_repo.delete(knowledge_base_id)

        if kb_type == RagType.DOCUMENT.value:
            try:
                drop_collection(kb_name)
            except Exception as e:
                logger.error("删除 Milvus 集合失败: %s", e)
        elif kb_type == RagType.GRAPH.value:
            try:
                from app.module.rag.service.strategy.graph_strategy import GraphKnowledgeBaseStrategy
                import shutil
                from pathlib import Path
                from app.core.config import settings
                workspace_path = Path(settings.rag_storage_dir) / kb_name
                if workspace_path.exists():
                    shutil.rmtree(workspace_path)
                    logger.info("已删除知识图谱 workspace: %s", kb_name)
                GraphKnowledgeBaseStrategy.clear_cache(kb_name)
            except Exception as e:
                logger.error("删除知识图谱 workspace 失败: %s", e)

        await self.db.commit()

    async def get_by_id(self, knowledge_base_id: str) -> KnowledgeBaseResp:
        """获取知识库详情"""
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        file_count = await self.file_repo.count_by_knowledge_base(knowledge_base_id)
        chunk_count = await self.file_repo.count_chunks_by_knowledge_base(knowledge_base_id)

        data = self._kb_to_dict(knowledge_base)
        data.update({
            "file_count": file_count,
            "chunk_count": chunk_count,
            "embedding": await self._get_model_config(knowledge_base.embedding_model),
            "chat": await self._get_model_config(knowledge_base.chat_model),
        })
        return KnowledgeBaseResp(**data)

    @staticmethod
    def _kb_to_dict(kb: KnowledgeBase) -> dict:
        """知识库实体转字典"""
        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "type": kb.type,
            "embedding_model": kb.embedding_model,
            "chat_model": kb.chat_model,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at,
            "created_by": kb.created_by,
            "updated_by": kb.updated_by,
        }

    async def _get_model_config(self, model_id: Optional[str]) -> Optional[ModelConfig]:
        """获取模型配置"""
        if not model_id:
            return None

        result = await self.db.execute(
            select(Models).where(
                Models.id == model_id,
                (Models.is_deleted == False) | (Models.is_deleted.is_(None))
            )
        )
        model = result.scalar_one_or_none()
        return ModelConfig.model_validate(model) if model else None

    async def list(self, request: KnowledgeBaseQueryReq) -> PagedResponse:
        """分页查询知识库列表"""
        items, total = await self.kb_repo.list(
            keyword=request.keyword,
            rag_type=request.type,
            page=request.page,
            page_size=request.page_size,
        )

        responses = []
        for item in items:
            file_count = await self.file_repo.count_by_knowledge_base(item.id)
            chunk_count = await self.file_repo.count_chunks_by_knowledge_base(item.id)
            data = self._kb_to_dict(item)
            data.update({
                "file_count": file_count,
                "chunk_count": chunk_count,
            })
            responses.append(KnowledgeBaseResp(**data))

        return PagedResponse.create(
            content=responses,
            total_elements=total,
            page=request.page,
            size=request.page_size,
        )

    # ==================== 文件管理 ====================

    async def add_files(
        self,
        request: AddFilesReq,
        background_tasks: BackgroundTasks = None,
    ) -> dict:
        """添加文件到知识库

        验证知识库、创建文件记录、启动后台处理。
        数据库提交后立即返回，不等待文件处理完成。

        Args:
            request: 添加文件请求
            background_tasks: FastAPI 后台任务

        Returns:
            包含成功和跳过文件数量的字典
        """
        knowledge_base = await self.kb_repo.get_by_id(request.knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        rag_files, skipped_file_ids = await self._create_rag_files(request)

        await self.db.commit()

        if rag_files and background_tasks:
            kb_type = knowledge_base.type if knowledge_base.type else "DOCUMENT"
            self.file_processor.start_background_processing(
                background_tasks=background_tasks,
                knowledge_base_id=str(knowledge_base.id),
                knowledge_base_name=str(knowledge_base.name),
                knowledge_base_type=str(kb_type),
                request_data=request.model_dump(),
            )

        return {
            "success_count": len(rag_files),
            "skipped_count": len(skipped_file_ids),
            "skipped_file_ids": skipped_file_ids,
        }

    async def _create_rag_files(self, request: AddFilesReq) -> Tuple[List[RagFile], List[str]]:
        """创建 RAG 文件记录"""
        if not request.files:
            raise BusinessError(ErrorCodes.BAD_REQUEST, "文件列表不能为空")

        rag_files = []
        skipped_file_ids = []

        for file_info in request.files:
            try:
                result = await self.db.execute(
                    select(DatasetFiles).where(DatasetFiles.id == file_info.id)
                )
                dataset_file = result.scalar_one_or_none()

                if not dataset_file:
                    logger.warning("文件不存在，跳过: file_id=%s", file_info.id)
                    skipped_file_ids.append(file_info.id)
                    continue

                rag_file = RagFile(
                    id=str(uuid.uuid4()),
                    knowledge_base_id=request.knowledge_base_id,
                    file_name=dataset_file.file_name,
                    file_id=file_info.id,
                    file_metadata={
                        "process_type": request.process_type.value,
                        "dataset_id": dataset_file.dataset_id,
                        "file_path": dataset_file.file_path,
                    },
                    status=FileStatus.UNPROCESSED,
                )
                rag_files.append(rag_file)

            except Exception as e:
                logger.error("处理文件信息失败: file_id=%s, error=%s", file_info.id, e)
                skipped_file_ids.append(file_info.id)

        if rag_files:
            await self.file_repo.batch_create(rag_files)
            logger.info("成功添加 %d 个文件到知识库", len(rag_files))

        return rag_files, skipped_file_ids

    async def list_files(self, knowledge_base_id: str, request: RagFileReq) -> PagedResponse:
        """获取知识库文件列表"""
        if not await self.kb_repo.get_by_id(knowledge_base_id):
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        items, total = await self.file_repo.list_by_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            keyword=request.keyword,
            status=request.status,
            page=request.page,
            page_size=request.page_size,
        )

        responses = [RagFileResp.model_validate(item) for item in items]

        return PagedResponse.create(
            content=responses,
            total_elements=total,
            page=request.page,
            size=request.page_size,
        )

    async def delete_files(self, knowledge_base_id: str, request: DeleteFilesReq) -> None:
        """删除知识库文件

        Args:
            knowledge_base_id: 知识库 ID
            request: 删除文件请求
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        if not request.file_ids:
            raise BusinessError(ErrorCodes.BAD_REQUEST, "文件ID列表不能为空")

        kb_type = knowledge_base.type
        kb_name = str(knowledge_base.name)

        rag_files = []
        for file_id in request.file_ids:
            rag_file = await self.file_repo.get_by_id(file_id)
            if rag_file:
                rag_files.append(rag_file)

        if rag_files:
            if kb_type == RagType.DOCUMENT.value:
                try:
                    delete_chunks_by_rag_file_ids(
                        kb_name,
                        [r.id for r in rag_files],
                    )
                except Exception as e:
                    logger.error("删除 Milvus 数据失败: %s", e)
            elif kb_type == RagType.GRAPH.value:
                try:
                    from app.module.rag.service.strategy.graph_strategy import GraphKnowledgeBaseStrategy
                    strategy = GraphKnowledgeBaseStrategy(self.db)
                    rag_instance = await strategy._get_or_create_graph_rag(knowledge_base)
                    for rag_file in rag_files:
                        doc_id = str(rag_file.id)
                        await rag_instance.adelete_by_doc_id(doc_id)
                        logger.info("已从知识图谱删除文件: %s, doc_id=%s", rag_file.file_name, doc_id)
                except Exception as e:
                    logger.error("删除知识图谱数据失败: %s", e)

        for file_id in request.file_ids:
            try:
                await self.file_repo.delete(file_id)
            except Exception as e:
                logger.error("删除数据库记录失败: %s, error=%s", file_id, e)

        await self.db.commit()
        logger.info("成功删除 %d 个文件", len(rag_files))

    async def update_chunk(
        self,
        knowledge_base_id: str,
        chunk_id: str,
        text: str,
        metadata: dict = None,
    ) -> None:
        """更新指定分块的文本和元数据

        Args:
            knowledge_base_id: 知识库 ID
            chunk_id: 分块 ID
            text: 新的文本内容
            metadata: 新的元数据（可选）
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        if knowledge_base.type != RagType.DOCUMENT.value:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                f"知识库类型 {knowledge_base.type} 不支持分块更新"
            )

        from app.module.system.service.common_service import get_model_by_id
        import asyncio

        embedding_entity = await get_model_by_id(self.db, knowledge_base.embedding_model)
        if not embedding_entity:
            raise BusinessError(ErrorCodes.RAG_MODEL_NOT_FOUND)

        embedding = EmbeddingFactory.create_embeddings(
            model_name=str(embedding_entity.model_name),
            base_url=getattr(embedding_entity, "base_url", None),
            api_key=getattr(embedding_entity, "api_key", None),
        )

        await asyncio.to_thread(
            update_chunk_by_id,
            collection_name=str(knowledge_base.name),
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
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        if knowledge_base.type != RagType.DOCUMENT.value:
            raise BusinessError(
                ErrorCodes.RAG_INVALID_REQUEST,
                f"知识库类型 {knowledge_base.type} 不支持分块删除"
            )

        import asyncio
        rag_file_id = await asyncio.to_thread(
            delete_chunk_by_id,
            collection_name=str(knowledge_base.name),
            chunk_id=chunk_id,
        )

        if rag_file_id:
            rag_file = await self.file_repo.get_by_id(rag_file_id)
            if rag_file and rag_file.chunk_count and rag_file.chunk_count > 0:
                rag_file.chunk_count = rag_file.chunk_count - 1
                await self.db.commit()

        logger.info(
            "成功删除分块: kb=%s chunk_id=%s",
            knowledge_base_id, chunk_id
        )
