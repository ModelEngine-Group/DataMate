"""
Operator Release Repository
算子发布版本数据访问层
"""
from typing import List

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.operator import OperatorRelease
from app.module.operator.schema import OperatorReleaseDto


class OperatorReleaseRepository:
    """算子发布版本数据访问层"""

    def __init__(self, model: OperatorRelease):
        self.model = model

    async def find_all_by_operator_id(
        self,
        operator_id: str,
        db: AsyncSession
    ) -> List[OperatorRelease]:
        """查询算子的所有发布版本"""
        result = await db.execute(
            select(OperatorRelease)
            .where(OperatorRelease.id == operator_id)
            .order_by(OperatorRelease.release_date.desc())
        )
        return result.scalars().all()

    async def insert(
        self,
        dto: OperatorReleaseDto,
        db: AsyncSession
    ) -> None:
        """插入发布版本"""
        entity = OperatorRelease(
            id=dto.id,
            version=dto.version,
            release_date=dto.release_date,
            changelog=dto.changelog
        )
        db.add(entity)

    async def update(
        self,
        dto: OperatorReleaseDto,
        db: AsyncSession
    ) -> None:
        """更新发布版本"""
        result = await db.execute(
            select(OperatorRelease)
            .where(
                and_(
                    OperatorRelease.id == dto.id,
                    OperatorRelease.version == dto.version
                )
            )
        )
        entity = result.scalar_one_or_none()
        if entity:
            entity.changelog = dto.changelog
            entity.release_date = dto.release_date

    async def delete(self, operator_id: str, db: AsyncSession) -> None:
        """删除算子的所有发布版本"""
        await db.execute(
            delete(OperatorRelease)
            .where(OperatorRelease.id == operator_id)
        )
