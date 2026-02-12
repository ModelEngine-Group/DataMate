"""
Category API Routes
分类 API 路由
"""
from fastapi import APIRouter, Depends

from app.db.models.operator import Category, CategoryRelation, Operator
from app.db.session import get_db
from app.module.operator.repository import (
    CategoryRepository,
    CategoryRelationRepository,
)
from app.module.operator.repository.operator_repository import OperatorRepository
from app.module.operator.schema import CategoryTreePagedResponse
from app.module.operator.schema.category import PaginatedCategoryTree
from app.module.operator.service import CategoryService
from app.module.shared.schema import StandardResponse

router = APIRouter(prefix="/categories", tags=["Category"])


def get_category_service() -> CategoryService:
    """获取分类服务实例"""
    return CategoryService(
        category_repo=CategoryRepository(Category()),
        category_relation_repo=CategoryRelationRepository(CategoryRelation()),
        operator_repo=OperatorRepository(Operator()),
    )


@router.get(
    "/tree",
    response_model=StandardResponse[PaginatedCategoryTree],
    summary="获取分类树",
    description="获取算子树状分类结构，包含分组维度（如语言、模态）及资源统计数量",
    tags=['mcp']
)
async def get_category_tree(
    service: CategoryService = Depends(get_category_service),
    db=Depends(get_db)
):
    """获取分类树"""
    result = await service.get_all_categories(db)

    return StandardResponse(
        code="0",
        message="success",
        data=PaginatedCategoryTree(
            page=0,
            size=len(result.categories),
            total_elements=len(result.categories),
            total_pages=1,
            star_count=result.star_count,
            content=result.categories,
        ))
