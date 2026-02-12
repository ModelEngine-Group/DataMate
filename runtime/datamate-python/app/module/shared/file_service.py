"""
File Service
文件服务，处理文件上传、分片上传等功能
"""
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger
from app.db.models.chunk_upload import ChunkUploadPreRequest
from app.module.shared.chunk_upload_repository import ChunkUploadRepository
from app.module.shared.chunks_saver import ChunksSaver
from app.module.shared.file_models import (
    ChunkUploadRequestDto,
    FileUploadResult,
)

logger = get_logger(__name__)


class FileService:
    """文件服务"""

    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(
        self,
        chunk_upload_repo: ChunkUploadRepository,
    ):
        self.chunk_upload_repo = chunk_upload_repo

    async def pre_upload(
        self,
        upload_path: str,
        service_id: str,
        db_session,
        check_info: Optional[str] = None
    ) -> str:
        """
        预上传

        Args:
            upload_path: 上传路径
            service_id: 服务ID
            check_info: 业务信息

        Returns:
            预上传请求ID
        """
        req_id = str(uuid.uuid4())
        timeout = datetime.utcnow().replace(
            microsecond=0
        ) + timedelta(seconds=self.DEFAULT_TIMEOUT_SECONDS)

        pre_request = ChunkUploadPreRequest(
            id=req_id,
            total_file_num=1,
            uploaded_file_num=0,
            upload_path=upload_path,
            timeout=timeout,
            service_id=service_id,
            check_info=check_info,
        )

        await self.chunk_upload_repo.insert(pre_request, db_session)
        return req_id

    async def chunk_upload(
        self,
        upload_request: ChunkUploadRequestDto,
        upload_path: str,
        file_content: bytes,
        db_session,
    ) -> FileUploadResult:
        """
        分片上传

        Args:
            upload_request: 上传请求
            upload_path: 上传路径
            file_content: 文件内容
            db_session: 数据库会话

        Returns:
            上传结果
        """
        upload_request.file_size = len(file_content)

        pre_request = await self.chunk_upload_repo.find_by_id(
            upload_request.req_id, db_session
        )

        if pre_request is None:
            logger.error(f"pre-upload request not found: {upload_request.req_id}")
            raise ValueError("Pre-upload request not found")

        if pre_request.is_upload_complete():
            logger.error(f"upload already complete: {upload_request.req_id}")
            raise ValueError("Upload already complete")

        if pre_request.is_request_timeout():
            logger.error(f"upload request timeout: {upload_request.req_id}")
            raise ValueError("Upload request timeout")

        saved_file_path = None

        if upload_request.total_chunk_num > 1:
            saved_file_path = await self._upload_chunk(
                upload_request, pre_request, upload_path, file_content
            )
        else:
            saved_file_path = await self._upload_file(
                upload_request, pre_request, upload_path, file_content
            )

        update_count = await self.chunk_upload_repo.update(pre_request, db_session)

        if update_count == 0:
            logger.error(f"failed to update pre-request: {upload_request.req_id}")
            raise ValueError("Failed to update pre-upload request")

        is_finish = pre_request.uploaded_file_num == pre_request.total_file_num

        if is_finish:
            temp_dir = os.path.join(
                upload_path,
                ChunksSaver.TEMP_DIR_NAME_FORMAT % pre_request.id
            )
            try:
                ChunksSaver.delete_folder(temp_dir)
            except Exception as e:
                logger.warning(f"failed to delete temp dir: {temp_dir}, error: {e}")

            await self.chunk_upload_repo.delete_by_id(pre_request.id, db_session)

        return FileUploadResult(
            is_all_files_uploaded=is_finish,
            check_info=pre_request.check_info,
            saved_file_path=str(saved_file_path) if saved_file_path else None,
            file_name=upload_request.file_name,
        )

    async def _upload_file(
        self,
        upload_request: ChunkUploadRequestDto,
        pre_request: ChunkUploadPreRequest,
        upload_path: str,
        file_content: bytes
    ) -> Path:
        """上传单文件"""
        saved_file = ChunksSaver.save_file(
            upload_request, upload_path, file_content
        )

        pre_request.timeout = datetime.utcnow().replace(
            microsecond=0
        ) + timedelta(seconds=self.DEFAULT_TIMEOUT_SECONDS)
        pre_request.increment_uploaded_file_num()

        return saved_file

    async def _upload_chunk(
        self,
        upload_request: ChunkUploadRequestDto,
        pre_request: ChunkUploadPreRequest,
        upload_path: str,
        file_content: bytes
    ) -> Optional[Path]:
        """上传分片"""
        saved_file = ChunksSaver.save(
            upload_request, pre_request.id, upload_path, file_content
        )

        if saved_file is not None:
            pre_request.increment_uploaded_file_num()
            return saved_file

        pre_request.timeout = datetime.utcnow().replace(
            microsecond=0
        ) + timedelta(seconds=self.DEFAULT_TIMEOUT_SECONDS)
        return None
