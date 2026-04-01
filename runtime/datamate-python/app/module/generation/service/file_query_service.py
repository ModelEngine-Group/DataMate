"""
文件查询服务 - 负责文件任务相关的查询操作
"""
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import DataSynthesisFileInstance
from app.module.generation.schema.generation import (
    DataSynthesisFileTaskItem,
    PagedDataSynthesisFileTaskResponse,
)


class FileQueryService:
    """文件查询服务 - 负责文件任务相关的查询操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, file_id: str) -> DataSynthesisFileInstance | None:
        """
        根据 ID 获取文件任务

        Args:
            file_id: 文件任务 ID

        Returns:
            文件任务实例，不存在则返回 None
        """
        return await self.db.get(DataSynthesisFileInstance, file_id)

    async def list_by_task(
        self, task_id: str, page: int, page_size: int
    ) -> Tuple[List[DataSynthesisFileTaskItem], int]:
        """
        分页查询任务下的文件任务列表

        Args:
            task_id: 任务 ID
            page: 页码
            page_size: 每页数量

        Returns:
            (文件任务列表, 总数)
        """
        base_query = select(DataSynthesisFileInstance).where(
            DataSynthesisFileInstance.synthesis_instance_id == task_id
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one() or 0

        offset = max(page, 1) - 1
        limit = max(page_size, 1)
        result = await self.db.execute(
            base_query.offset(offset * limit).limit(limit)
        )
        rows = result.scalars().all()

        items = [DataSynthesisFileTaskItem.model_validate(row) for row in rows]
        return items, total
