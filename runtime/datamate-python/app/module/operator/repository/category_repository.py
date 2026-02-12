"""
Category Repository
分类数据访问层
"""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.operator import Category
from app.module.operator.schema import CategoryDto


class CategoryRepository:
    """分类数据访问层"""

    def __init__(self, model: Category):
        self.model = model

    async def find_all(self, db: AsyncSession) -> List[Category]:
        """查询所有分类"""
        result = await db.execute(select(Category))
        return result.scalars().all()
