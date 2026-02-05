from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
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
        """Count results by instance ID (completed, failed)"""
        total_query = select(self.model).where(self.model.instance_id == instance_id)
        completed_query = total_query.where(self.model.status == "COMPLETED")
        failed_query = total_query.where(self.model.status == "FAILED")

        total = len((await db.execute(total_query)).scalars().all())
        completed = len((await db.execute(completed_query)).scalars().all())
        failed = len((await db.execute(failed_query)).scalars().all())

        return (completed, failed)

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
