import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.module.cleaning.schema import (
    CleaningTemplateDto,
    CreateCleaningTemplateRequest,
    UpdateCleaningTemplateRequest,
)
from app.module.cleaning.service import CleaningTemplateService
from app.module.shared.schema import StandardResponse, PaginatedData

logger = get_logger(__name__)

router = APIRouter(prefix="/cleaning/templates", tags=["Cleaning Templates"])


def _get_operator_service():
    """Get operator service"""
    from app.module.operator.service import OperatorService
    from app.module.operator.repository import (
        OperatorRepository,
        CategoryRelationRepository,
        OperatorReleaseRepository,
    )
    from app.module.operator.parsers import ParserHolder
    from app.module.shared.file_service import FileService
    from app.module.shared.chunk_upload_repository import ChunkUploadRepository

    return OperatorService(
        operator_repo=OperatorRepository(None),
        category_relation_repo=CategoryRelationRepository(None),
        operator_release_repo=OperatorReleaseRepository(None),
        parser_holder=ParserHolder(),
        file_service=FileService(ChunkUploadRepository()),
    )


def _get_template_service(db: AsyncSession) -> CleaningTemplateService:
    """Get cleaning template service instance"""
    from app.module.cleaning.service import CleaningTaskValidator
    from app.module.cleaning.repository import (
        CleaningTemplateRepository,
        OperatorInstanceRepository,
    )

    operator_service = _get_operator_service()

    template_repo = CleaningTemplateRepository(None)

    return CleaningTemplateService(
        template_repo=template_repo,
        operator_instance_repo=OperatorInstanceRepository(None),
        operator_service=operator_service,
        validator=CleaningTaskValidator(task_repo=None, template_repo=template_repo),
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[CleaningTemplateDto]],
    summary="查询清洗模板列表",
    description="分页查询清洗模板"
)
async def get_cleaning_templates(
    page: int = Query(1, description="页码"),
    size: int = Query(20, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db),
):
    """Query cleaning templates with pagination"""
    from app.db.models.cleaning import CleaningTemplate

    template_service = _get_template_service(db)

    query = select(CleaningTemplate)

    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(
            CleaningTemplate.name.ilike(keyword_pattern) | CleaningTemplate.description.ilike(keyword_pattern)
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    items = await template_service.get_templates(db, keyword)

    total_pages = math.ceil(total / size) if total > 0 else 0

    return StandardResponse(
        code="0",
        message="success",
        data=PaginatedData(
            content=items,
            total_elements=total,
            total_pages=total_pages,
            page=page,
            size=size,
        )
    )


@router.post(
    "",
    response_model=StandardResponse[CleaningTemplateDto],
    summary="创建清洗模板",
    description="创建新的清洗模板"
)
async def create_cleaning_template(
    request: CreateCleaningTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create cleaning template"""
    template_service = _get_template_service(db)

    template = await template_service.create_template(db, request)
    await db.commit()

    return StandardResponse(code="0", message="success", data=template)


@router.get(
    "/{template_id}",
    response_model=StandardResponse[CleaningTemplateDto],
    summary="获取清洗模板详情",
    description="根据ID获取清洗模板详细信息"
)
async def get_cleaning_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get cleaning template by ID"""
    template_service = _get_template_service(db)

    template = await template_service.get_template(db, template_id)
    return StandardResponse(code="0", message="success", data=template)


@router.put(
    "/{template_id}",
    response_model=StandardResponse[CleaningTemplateDto],
    summary="更新清洗模板",
    description="更新清洗模板信息"
)
async def update_cleaning_template(
    template_id: str,
    request: UpdateCleaningTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update cleaning template"""
    template_service = _get_template_service(db)

    template = await template_service.update_template(db, template_id, request)
    await db.commit()

    return StandardResponse(code="0", message="success", data=template)


@router.delete(
    "/{template_id}",
    response_model=StandardResponse[str],
    summary="删除清洗模板",
    description="删除指定的清洗模板"
)
async def delete_cleaning_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete cleaning template"""
    template_service = _get_template_service(db)
    await template_service.delete_template(db, template_id)
    await db.commit()

    return StandardResponse(code="0", message="success", data=template_id)
