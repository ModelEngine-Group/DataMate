"""
Category Service
分类服务层
"""
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.module.operator.repository import (
    CategoryRepository,
    CategoryRelationRepository,
)
from app.module.operator.schema import (
    CategoryDto,
    CategoryTreeResponse,
    CategoryTreePagedResponse,
)
from app.db.models.operator import Operator
from app.module.operator.repository.operator_repository import OperatorRepository


class CategoryService:
    """分类服务"""

    def __init__(
        self,
        category_repo: CategoryRepository,
        category_relation_repo: CategoryRelationRepository,
        operator_repo: OperatorRepository,
    ):
        self.category_repo = category_repo
        self.category_relation_repo = category_relation_repo
        self.operator_repo = operator_repo

    async def get_all_categories(
        self,
        db: AsyncSession
    ) -> CategoryTreePagedResponse:
        """获取所有分类（树状结构）"""
        # Get all categories
        all_categories = await self.category_repo.find_all(db)
        category_map = {c.id: c for c in all_categories}

        # Get all relations and count operators per category
        all_relations = await self.category_relation_repo.find_all(db)
        relation_map = {}
        for rel in all_relations:
            if rel.category_id not in relation_map:
                relation_map[rel.category_id] = 0
            relation_map[rel.category_id] += 1

        # Group by parent_id
        grouped_by_parent = {}
        for cat in all_categories:
            if cat.parent_id != "0":
                if cat.parent_id not in grouped_by_parent:
                    grouped_by_parent[cat.parent_id] = []
                grouped_by_parent[cat.parent_id].append(cat)

        # Build category trees
        parent_ids = sorted(
            grouped_by_parent.keys(),
            key=lambda pid: pid
        )

        category_trees = []
        for parent_id in parent_ids:
            group = grouped_by_parent[parent_id]
            parent_category = category_map[parent_id]

            # Build DTOs for children
            child_dtos = []
            total_count = 0
            for cat in sorted(group, key=lambda c: c.created_at or 0):
                cat_dto = CategoryDto(
                    id=cat.id,
                    name=cat.name,
                    value=cat.value,
                    type=cat.type,
                    parent_id=cat.parent_id,
                    count=relation_map.get(cat.id, 0),
                    created_at=cat.created_at,
                )
                child_dtos.append(cat_dto)
                total_count += cat_dto.count

            tree = CategoryTreeResponse(
                id=parent_id,
                name=parent_category.name,
                count=total_count,
                categories=child_dtos,
            )
            category_trees.append(tree)

        # Get star count
        star_count = await self.operator_repo.count_by_star(True, db)

        return CategoryTreePagedResponse(
            star_count=star_count,
            categories=category_trees,
        )
