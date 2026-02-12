"""
Chunk Upload Repository
分片上传数据访问层
"""
from typing import Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chunk_upload import ChunkUploadPreRequest
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChunkUploadRepository:
    """分片上传数据访问层"""

    async def find_by_id(
        self,
        req_id: str,
        db: AsyncSession
    ) -> Optional[ChunkUploadPreRequest]:
        """根据ID查询"""
        result = await db.execute(
            select(ChunkUploadPreRequest).where(ChunkUploadPreRequest.id == req_id)
        )
        return result.scalar_one_or_none()

    async def find_by_service_id(
        self,
        service_id: str,
        db: AsyncSession
    ) -> List[ChunkUploadPreRequest]:
        """根据服务ID查询"""
        result = await db.execute(
            select(ChunkUploadPreRequest).where(
                ChunkUploadPreRequest.service_id == service_id
            )
        )
        return result.scalars().all()

    async def find_all(self, db: AsyncSession) -> List[ChunkUploadPreRequest]:
        """查询所有"""
        result = await db.execute(select(ChunkUploadPreRequest))
        return result.scalars().all()

    async def insert(
        self,
        request: ChunkUploadPreRequest,
        db: AsyncSession
    ) -> None:
        """插入"""
        db.add(request)

    async def update(
        self,
        request: ChunkUploadPreRequest,
        db: AsyncSession
    ) -> int:
        """更新"""
        from datetime import datetime, timezone
        result = await db.execute(
            update(ChunkUploadPreRequest)
            .where(ChunkUploadPreRequest.id == request.id)
            .values(
                uploaded_file_num=request.uploaded_file_num,
                timeout=request.timeout,
            )
        )
        return result.rowcount

    async def delete_by_id(
        self,
        req_id: str,
        db: AsyncSession
    ) -> int:
        """根据ID删除"""
        result = await db.execute(
            delete(ChunkUploadPreRequest).where(ChunkUploadPreRequest.id == req_id)
        )
        return result.rowcount

    async def delete_by_service_id(
        self,
        service_id: str,
        db: AsyncSession
    ) -> int:
        """根据服务ID删除"""
        result = await db.execute(
            delete(ChunkUploadPreRequest).where(
                ChunkUploadPreRequest.service_id == service_id
            )
        )
        return result.rowcount
