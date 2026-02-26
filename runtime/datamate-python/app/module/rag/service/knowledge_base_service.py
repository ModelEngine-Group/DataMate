"""
知识库业务服务

实现知识库的 CRUD 操作和文件管理。
对应 Java: com.datamate.rag.indexer.application.KnowledgeBaseService
"""
import logging
import uuid
from typing import List, Tuple

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.db.models.dataset_management import DatasetFiles
from app.db.models.knowledge_gen import KnowledgeBase, RagFile, FileStatus
from app.module.rag.infra.vectorstore import drop_collection, rename_collection, delete_chunks_by_rag_file_ids
from app.module.rag.repository import KnowledgeBaseRepository, RagFileRepository
from app.module.rag.schema.request import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseUpdateReq,
    KnowledgeBaseQueryReq,
    AddFilesReq,
    DeleteFilesReq,
    RagFileReq,
)
from app.module.rag.schema.response import KnowledgeBaseResp, PagedResponse, RagFileResp
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

        old_name = knowledge_base.name
        knowledge_base.name = request.name
        knowledge_base.description = request.description

        await self.kb_repo.update(knowledge_base)

        if old_name != request.name:
            try:
                rename_collection(old_name, request.name)
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

        await self.file_repo.delete_by_knowledge_base(knowledge_base_id)
        await self.kb_repo.delete(knowledge_base_id)

        try:
            drop_collection(knowledge_base.name)
        except Exception as e:
            logger.error("删除 Milvus 集合失败: %s", e)

        await self.db.commit()

    async def get_by_id(self, knowledge_base_id: str) -> KnowledgeBaseResp:
        """获取知识库详情

        Args:
            knowledge_base_id: 知识库 ID

        Returns:
            知识库响应对象
        """
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        file_count = await self.file_repo.count_by_knowledge_base(knowledge_base_id)
        chunk_count = await self.file_repo.count_chunks_by_knowledge_base(knowledge_base_id)

        return KnowledgeBaseResp(
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
            updated_by=knowledge_base.updated_by,
        )

    async def list(self, request: KnowledgeBaseQueryReq) -> PagedResponse:
        """分页查询知识库列表

        Args:
            request: 查询请求

        Returns:
            分页响应
        """
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
            responses.append(KnowledgeBaseResp(
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
                updated_by=item.updated_by,
            ))

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

        存入数据库后立即返回，后台异步处理文件。

        Args:
            request: 添加文件请求
            background_tasks: FastAPI 后台任务

        Returns:
            包含成功和跳过文件数量的字典
        """
        knowledge_base = await self.kb_repo.get_by_id(request.knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 添加文件记录
        rag_files, skipped_file_ids = await self._create_rag_files(request)

        await self.db.commit()

        # 启动后台处理
        if rag_files and background_tasks:
            self.file_processor.start_background_processing(
                background_tasks=background_tasks,
                knowledge_base_id=knowledge_base.id,
                knowledge_base_name=knowledge_base.name,
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
        """获取知识库文件列表

        Args:
            knowledge_base_id: 知识库 ID
            request: 查询请求

        Returns:
            分页响应
        """
        if not await self.kb_repo.get_by_id(knowledge_base_id):
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        items, total = await self.file_repo.list_by_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            keyword=request.keyword,
            status=request.status,
            page=request.page,
            page_size=request.page_size,
        )

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
            updated_by=item.updated_by,
        ) for item in items]

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

        # 获取文件列表
        rag_files = []
        for file_id in request.file_ids:
            rag_file = await self.file_repo.get_by_id(file_id)
            if rag_file:
                rag_files.append(rag_file)

        # 删除 Milvus 数据
        if rag_files:
            try:
                delete_chunks_by_rag_file_ids(
                    knowledge_base.name,
                    [r.id for r in rag_files],
                )
            except Exception as e:
                logger.error("删除 Milvus 数据失败: %s", e)

        # 删除数据库记录
        for file_id in request.file_ids:
            try:
                await self.file_repo.delete(file_id)
            except Exception as e:
                logger.error("删除数据库记录失败: %s, error=%s", file_id, e)

        await self.db.commit()
        logger.info("成功删除 %d 个文件", len(rag_files))
