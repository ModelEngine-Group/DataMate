"""
Category Schemas
分类 Schema 定义
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.module.shared.schema import BaseResponseModel, PaginatedData


class CategoryDto(BaseResponseModel):
    """分类 DTO"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    value: Optional[str] = Field(None, description="分类值")
    type: Optional[str] = Field(None, description="分类类型")
    parent_id: Optional[str] = Field(None, description="父分类ID")
    count: Optional[int] = Field(0, description="算子数量")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class CategoryTreeResponse(BaseResponseModel):
    """分类树响应"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    count: int = Field(0, description="算子总数")
    categories: List[CategoryDto] = Field(default_factory=list, description="子分类列表")


class CategoryTreePagedResponse(BaseResponseModel):
    """分类树分页响应"""
    star_count: int = Field(0, description="收藏的算子数量")
    categories: List[CategoryTreeResponse] = Field(default_factory=list, description="分类树列表")


class PaginatedCategoryTree(PaginatedData):
    star_count: int = Field(0, description="收藏的算子数量")


class CategoryRelationDto(BaseResponseModel):
    """分类关系 DTO"""
    category_id: str = Field(..., description="分类ID")
    operator_id: str = Field(..., description="算子ID")
