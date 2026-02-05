import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models.cleaning import OperatorInstance


class OperatorInstanceRepository:
    """Repository for operator instance operations"""

    def __init__(self, model=None):
        self.model = model if model else OperatorInstance

    async def find_operator_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str
    ) -> List[OperatorInstance]:
        """Query operator instances by instance ID"""
        query = select(self.model).where(self.model.instance_id == instance_id)
        query = query.order_by(self.model.op_index.asc())
        result = await db.execute(query)
        return result.scalars().all()

    async def find_instance_by_instance_id(
        self,
        db: AsyncSession,
        instance_id: str
    ) -> List[OperatorInstance]:
        """Query instances for template (same as find_operator_by_instance_id)"""
        return await self.find_operator_by_instance_id(db, instance_id)

    async def insert_instance(
        self,
        db: AsyncSession,
        instance_id: str,
        instances: List
    ) -> None:
        """Insert operator instances"""
        from app.db.models.cleaning import OperatorInstance as OperatorInstanceModel
        
        for idx, instance in enumerate(instances):
            db_instance = OperatorInstanceModel(
                instance_id=instance_id,
                operator_id=instance.id,
                op_index=idx,
                settings_override=json.dumps(instance.overrides),
            )
            db.add(db_instance)
        await db.flush()

    async def delete_by_instance_id(self, db: AsyncSession, instance_id: str) -> None:
        """Delete instances by instance ID"""
        query = delete(self.model).where(self.model.instance_id == instance_id)
        await db.execute(query)
        await db.flush()
