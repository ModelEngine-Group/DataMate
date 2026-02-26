"""
文件管理服务

实现文件相关的业务逻辑
"""
import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.knowledge_gen import RagFile, FileStatus
from app.db.models.dataset_management import DatasetFiles
from app.module.rag.schema.request import AddFilesReq
from app.module.rag.repository import RagFileRepository, KnowledgeBaseRepository
from app.module.rag.infra.milvus.vectorstore import delete_chunks_by_rag_file_ids
from app.core.exception import BusinessError, ErrorCodes

import logging

logger = logging.getLogger(__name__)


class FileService:
    """文件管理服务类

    功能：
    1. 添加文件到知识库
    2. 删除文件
    3. 查询文件
    """

    def __init__(self, db: AsyncSession):
        """初始化服务

        Args:
            db: 数据库异步 session
        """
        self.db = db
        self.file_repo = RagFileRepository(db)
        self.kb_repo = KnowledgeBaseRepository(db)

    async def add_files(self, request: AddFilesReq) -> Tuple[List[RagFile], List[str]]:
        """添加文件到知识库

        Args:
            request: 添加文件请求

        Returns:
            (创建的 RAG 文件列表, 跳过的文件ID列表)

        Raises:
            BusinessError: 知识库不存在
        """
        # 验证知识库存在
        knowledge_base = await self.kb_repo.get_by_id(request.knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 验证文件列表不为空
        if not request.files or len(request.files) == 0:
            raise BusinessError(ErrorCodes.BAD_REQUEST, "文件列表不能为空")

        # 验证文件存在并创建 RAG 文件记录
        rag_files = []
        skipped_file_ids = []

        for file_info in request.files:
            try:
                # 根据 file_info.id (DatasetFile ID) 查询文件信息
                result = await self.db.execute(
                    select(DatasetFiles).where(DatasetFiles.id == file_info.id)
                )
                dataset_file = result.scalar_one_or_none()

                # 跳过不存在的文件
                if not dataset_file:
                    logger.warning(
                        f"文件不存在，跳过处理: file_id={file_info.id}"
                    )
                    skipped_file_ids.append(file_info.id)
                    continue

                # 创建 RAG 文件记录，存储 dataset_id 和 file_path 到 metadata
                rag_file = RagFile(
                    id=str(uuid.uuid4()),
                    knowledge_base_id=request.knowledge_base_id,
                    file_name=dataset_file.file_name,
                    file_id=file_info.id,
                    file_metadata={
                        "process_type": request.process_type.value,
                        "dataset_id": dataset_file.dataset_id,
                        "file_path": dataset_file.file_path
                    },
                    status=FileStatus.UNPROCESSED,
                )
                rag_files.append(rag_file)

            except Exception as e:
                logger.error(
                    f"处理文件信息失败: file_id={file_info.id}, error={e}"
                )
                skipped_file_ids.append(file_info.id)
                continue

        # 批量保存
        if rag_files:
            await self.file_repo.batch_create(rag_files)
            logger.info(f"成功添加 {len(rag_files)} 个文件到知识库: {knowledge_base.name}")

        if skipped_file_ids:
            logger.warning(f"跳过 {len(skipped_file_ids)} 个文件: {skipped_file_ids}")

        return rag_files, skipped_file_ids

    async def delete_files(
        self,
        knowledge_base_id: str,
        file_ids: List[str]
    ) -> None:
        """删除文件

        Args:
            knowledge_base_id: 知识库 ID
            file_ids: 文件 ID 列表

        Raises:
            BusinessError: 知识库不存在
        """
        # 验证文件列表不为空
        if not file_ids or len(file_ids) == 0:
            raise BusinessError(ErrorCodes.BAD_REQUEST, "文件ID列表不能为空")

        # 获取知识库
        knowledge_base = await self.kb_repo.get_by_id(knowledge_base_id)
        if not knowledge_base:
            raise BusinessError(ErrorCodes.RAG_KNOWLEDGE_BASE_NOT_FOUND)

        # 获取文件列表（需要删除 Milvus 数据）
        rag_files = []
        for file_id in file_ids:
            try:
                rag_file = await self.file_repo.get_by_id(file_id)
                if rag_file:
                    rag_files.append(rag_file)
                else:
                    logger.warning(f"文件不存在，跳过删除: {file_id}")
            except Exception as e:
                logger.error(f"查询文件失败: {file_id}, error={e}")
                continue

        # 删除 Milvus 中该文件对应的分块数据
        if rag_files:
            try:
                delete_chunks_by_rag_file_ids(
                    knowledge_base.name,
                    [r.id for r in rag_files],
                )
            except Exception as e:
                logger.error("删除 Milvus 数据失败: %s", e)
                # 继续删除数据库记录
        else:
            logger.warning("没有找到有效的文件，跳过 Milvus 数据删除")

        # 删除数据库记录
        deleted_count = 0
        for file_id in file_ids:
            try:
                await self.file_repo.delete(file_id)
                deleted_count += 1
            except Exception as e:
                logger.error(f"删除数据库记录失败: {file_id}, error={e}")
                continue

        logger.info(f"成功删除 {deleted_count} 个文件")
