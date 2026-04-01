"""
切片查询服务 - 负责切片相关的查询操作
"""
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import DataSynthesisChunkInstance
from app.module.generation.schema.generation import (
    DataSynthesisChunkItem,
    PagedDataSynthesisChunkResponse,
)


class ChunkQueryService:
    """切片查询服务 - 负责切片相关的查询操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, chunk_id: str) -> DataSynthesisChunkInstance | None:
        """
        根据 ID 获取切片

        Args:
            chunk_id: 切片 ID

        Returns:
            切片实例，不存在则返回 None
        """
        return await self.db.get(DataSynthesisChunkInstance, chunk_id)

    async def list_by_file(
        self, file_id: str, page: int, page_size: int
    ) -> Tuple[List[DataSynthesisChunkItem], int]:
        """
        分页查询文件任务下的切片列表

        Args:
            file_id: 文件任务 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (切片列表, 总数)
        """
        base_query = select(DataSynthesisChunkInstance).where(
            DataSynthesisChunkInstance.synthesis_file_instance_id == file_id
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one() or 0

        offset = max(page, 1) - 1
        limit = max(page_size, 1)
        result = await self.db.execute(
            base_query.order_by(DataSynthesisChunkInstance.chunk_index.asc())
            .offset(offset * limit)
            .limit(limit)
        )
        rows = result.scalars().all()

        items = [DataSynthesisChunkItem.model_validate(row) for row in rows]
        return items, total
