from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import DataSynthInstance
from app.module.generation.schema.generation import (
    DataSynthesisTaskItem,
    PagedDataSynthesisTaskResponse,
)


class TaskQueryService:
    """任务查询服务 - 专注于任务列表和详情查询"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_task(self, task_id: str) -> DataSynthInstance | None:
        """获取单个任务"""
        return await self.db.get(DataSynthInstance, task_id)

    async def list_tasks(
        self,
        page: int,
        page_size: int,
        synthesis_type: str | None = None,
        status: str | None = None,
        name: str | None = None,
    ) -> PagedDataSynthesisTaskResponse:
        """分页查询任务列表"""
        query = select(DataSynthInstance)

        if synthesis_type:
            query = query.where(DataSynthInstance.synth_type == synthesis_type)
        if status:
            query = query.where(DataSynthInstance.status == status)
        if name:
            query = query.where(DataSynthInstance.name.like(f"%{name}%"))

        query = query.order_by(DataSynthInstance.created_at.desc())

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one() or 0

        offset = max(page, 1) - 1
        limit = max(page_size, 1)
        result = await self.db.execute(query.offset(offset * limit).limit(limit))
        rows = result.scalars().all()

        items = [DataSynthesisTaskItem.from_orm_with_config(row) for row in rows]

        return PagedDataSynthesisTaskResponse(
            content=items,
            totalElements=total,
            totalPages=(total + page_size - 1) // page_size,
            page=page,
            size=page_size,
        )
