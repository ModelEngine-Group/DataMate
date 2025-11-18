"""
Annotation Template API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.module.shared.schema import StandardResponse
from app.module.annotation.schema import (
    CreateAnnotationTemplateRequest,
    UpdateAnnotationTemplateRequest,
    AnnotationTemplateResponse,
    AnnotationTemplateListResponse
)
from app.module.annotation.service.template import AnnotationTemplateService

router = APIRouter(prefix="/template", tags=["annotation/template"])

template_service = AnnotationTemplateService()


@router.post(
    "",
    response_model=StandardResponse[AnnotationTemplateResponse],
)
async def create_template(
    request: CreateAnnotationTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的标注模板
    
    - **name**: 模板名称（必填，最多100字符）
    - **description**: 模板描述（可选，最多500字符）
    - **dataType**: 数据类型（必填）
    - **labelingType**: 标注类型（必填）
    - **configuration**: 标注配置（必填，包含labels和objects）
    - **style**: 样式配置（默认horizontal）
    - **category**: 模板分类（默认custom）
    """
    template = await template_service.create_template(db, request)
    return StandardResponse(code=200, message="success", data=template)


@router.get(
    "/{template_id}",
    response_model=StandardResponse[AnnotationTemplateResponse],
)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取模板详情
    """
    template = await template_service.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return StandardResponse(code=200, message="success", data=template)


@router.get(
    "",
    response_model=StandardResponse[AnnotationTemplateListResponse],
)
async def list_template(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    category: Optional[str] = Query(None, description="分类筛选"),
    dataType: Optional[str] = Query(None, alias="dataType", description="数据类型筛选"),
    labelingType: Optional[str] = Query(None, alias="labelingType", description="标注类型筛选"),
    builtIn: Optional[bool] = Query(None, alias="builtIn", description="是否内置模板"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取模板列表，支持分页和筛选
    
    - **page**: 页码（从1开始）
    - **size**: 每页大小（1-100）
    - **category**: 模板分类筛选
    - **dataType**: 数据类型筛选
    - **labelingType**: 标注类型筛选
    - **builtIn**: 是否只显示内置模板
    """
    templates = await template_service.list_templates(
        db=db,
        page=page,
        size=size,
        category=category,
        data_type=dataType,
        labeling_type=labelingType,
        built_in=builtIn
    )
    return StandardResponse(code=200, message="success", data=templates)


@router.put(
    "/{template_id}",
    response_model=StandardResponse[AnnotationTemplateResponse],
)
async def update_template(
    template_id: str,
    request: UpdateAnnotationTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新模板信息
    
    所有字段都是可选的，只更新提供的字段
    """
    template = await template_service.update_template(db, template_id, request)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return StandardResponse(code=200, message="success", data=template)


@router.delete(
    "/{template_id}",
    response_model=StandardResponse[bool],
)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除模板（软删除）
    """
    success = await template_service.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return StandardResponse(code=200, message="success", data=True)
