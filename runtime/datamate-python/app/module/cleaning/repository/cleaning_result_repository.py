from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, Integer
from app.db.models.cleaning import CleaningResult
from app.module.cleaning.schema import CleaningResultDto


class CleaningResultRepository:
    """Repository for cleaning result operations"""

    def __init__(self, model=None):
        self.model = model if model else CleaningResult

    async def find_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str,
        status: Optional[str] = None
    ) -> List[CleaningResultDto]:
        """Query results by instance ID"""
        query = select(self.model).where(self.model.instance_id == instance_id)

        if status:
            query = query.where(self.model.status == status)

        result = await db.execute(query)
        results = result.scalars().all()

        return [
            CleaningResultDto(
                instance_id=res.instance_id,
                src_file_id=res.src_file_id,
                dest_file_id=res.dest_file_id,
                src_name=res.src_name,
                dest_name=res.dest_name,
                src_type=res.src_type,
                dest_type=res.dest_type,
                src_size=res.src_size,
                dest_size=res.dest_size,
                status=res.status,
                result=res.result
            )
            for res in results
        ]

    async def count_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str
    ) -> tuple[int, int]:
        """Count results by instance ID (completed, failed) using single SQL"""
        query = select(
            func.sum(func.cast(self.model.status == "COMPLETED", Integer)).label("completed"),
            func.sum(func.cast(self.model.status == "FAILED", Integer)).label("failed"),
        ).where(self.model.instance_id == instance_id)
        result = await db.execute(query)
        row = result.one()
        return (row.completed or 0, row.failed or 0)

    async def count_total_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str
    ) -> int:
        """Count total results by instance ID using efficient SQL COUNT"""
        query = select(func.count()).select_from(self.model).where(
            self.model.instance_id == instance_id
        )
        result = await db.scalar(query)
        return result or 0

    async def batch_count_by_instance_ids(
        self,
        db: AsyncSession,
        instance_ids: list[str]
    ) -> dict[str, tuple[int, int, int]]:
        """Batch count completed/failed/total for multiple instance IDs using single SQL.

        Returns dict: {instance_id: (completed, failed, total)}
        """
        if not instance_ids:
            return {}

        query = select(
            self.model.instance_id,
            func.sum(func.cast(self.model.status == "COMPLETED", Integer)).label("completed"),
            func.sum(func.cast(self.model.status == "FAILED", Integer)).label("failed"),
            func.count().label("total"),
        ).where(self.model.instance_id.in_(instance_ids)).group_by(self.model.instance_id)

        result = await db.execute(query)
        return {
            row.instance_id: (row.completed or 0, row.failed or 0, row.total or 0)
            for row in result.all()
        }

    async def delete_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str,
        status: Optional[str] = None
    ) -> None:
        """Delete results by instance ID"""
        query = delete(self.model).where(self.model.instance_id == instance_id)

        if status:
            query = query.where(self.model.status == status)

        await db.execute(query)
        await db.flush()
