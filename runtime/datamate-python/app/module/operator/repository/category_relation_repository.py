"""
Category Relation Repository
分类关系数据访问层
"""
from typing import List

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.operator import CategoryRelation
from app.module.operator.constants import CATEGORY_PREDEFINED_ID


class CategoryRelationRepository:
    """分类关系数据访问层"""

    def __init__(self, model: CategoryRelation):
        self.model = model

    async def find_all(self, db: AsyncSession) -> List[CategoryRelation]:
        """查询所有分类关系"""
        result = await db.execute(select(CategoryRelation))
        return result.scalars().all()

    async def batch_insert(
        self,
        operator_id: str,
        category_ids: List[str],
        db: AsyncSession
    ) -> None:
        """批量插入分类关系"""
        for category_id in category_ids:
            entity = CategoryRelation(
                category_id=category_id,
                operator_id=operator_id
            )
            db.add(entity)

    async def batch_update(
        self,
        operator_id: str,
        category_ids: List[str],
        db: AsyncSession
    ) -> None:
        """批量更新分类关系（先删除后插入）"""
        # Delete existing relations
        await db.execute(
            delete(CategoryRelation)
            .where(CategoryRelation.operator_id == operator_id)
        )
        # Insert new relations
        for category_id in category_ids:
            entity = CategoryRelation(
                category_id=category_id,
                operator_id=operator_id
            )
            db.add(entity)

    async def delete_by_operator_id(self, operator_id: str, db: AsyncSession) -> None:
        """根据算子ID删除分类关系"""
        await db.execute(
            delete(CategoryRelation)
            .where(CategoryRelation.operator_id == operator_id)
        )

    async def operator_is_predefined(self, operator_id: str, db: AsyncSession) -> bool:
        """检查算子是否为预定义算子"""
        result = await db.execute(
            select(CategoryRelation)
            .where(
                and_(
                    CategoryRelation.operator_id == operator_id,
                    CategoryRelation.category_id == CATEGORY_PREDEFINED_ID
                )
            )
        )
        return result.first() is not None
