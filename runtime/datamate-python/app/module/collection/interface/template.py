
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_collection import CollectionTemplate
from app.db.session import get_db
from app.module.collection.schema.collection import CollectionTemplateBase, converter_template_to_response
from app.module.shared.schema import StandardResponse, PaginatedData

router = APIRouter(
    prefix="/templates",
    tags=["data-collection/templates"],
)
logger = get_logger(__name__)


@router.get("", response_model=StandardResponse[PaginatedData[CollectionTemplateBase]])
async def list_templates(
    page: int = 1,
    size: int = 20,
    name: Optional[str] = Query(None, description="Fuzzy search by template name"),
    built_in: Optional[bool] = Query(None, description="Filter by system built-in template"),
    db: AsyncSession = Depends(get_db)
):
    """分页查询归集任务模板"""
    try:
        query = select(CollectionTemplate)

        if name:
            query = query.where(CollectionTemplate.name.ilike(f"%{name}%"))

        if built_in is not None:
            query = query.where(CollectionTemplate.built_in == built_in)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        offset = (page - 1) * size
        templates = (await db.execute(
            query.order_by(CollectionTemplate.created_at.desc())
            .offset(offset)
            .limit(size)
        )).scalars().all()

        items = [converter_template_to_response(tpl) for tpl in templates]
        total_pages = math.ceil(total / size) if total > 0 else 0

        return StandardResponse(
            code="0",
            message="Success",
            data=PaginatedData(
                content=items,
                total_elements=total,
                total_pages=total_pages,
                page=page,
                size=size,
            )
        )

    except Exception as e:
        logger.error(f"Failed to list collection templates: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")
