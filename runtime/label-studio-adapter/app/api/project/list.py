from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import math

from app.db.database import get_db
from app.services.dataset_mapping_service import DatasetMappingService
from app.schemas.dataset_mapping import DatasetMappingResponse
from app.schemas.common import StandardResponse, PaginatedData
from app.core.logging import get_logger
from . import project_router

logger = get_logger(__name__)

@project_router.get("/mappings/list", response_model=StandardResponse[PaginatedData[DatasetMappingResponse]])
async def list_mappings(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db)
):
    """
    查询所有映射关系（分页）
    
    返回所有有效的数据集映射关系（未被软删除的），支持分页查询
    """
    try:
        service = DatasetMappingService(db)
        
        # 计算 skip
        skip = (page - 1) * page_size
        
        logger.info(f"Listing mappings, page={page}, page_size={page_size}")
        
        # 获取数据和总数
        mappings, total = await service.get_all_mappings_with_count(
            skip=skip, 
            limit=page_size
        )
        
        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # 构造分页响应
        paginated_data = PaginatedData(
            page=page,
            size=page_size,
            total_elements=total,
            total_pages=total_pages,
            content=mappings
        )
        
        logger.info(f"Found {len(mappings)} mappings on page {page}, total: {total}")
        
        return StandardResponse(
            code=200,
            message="success",
            data=paginated_data
        )
        
    except Exception as e:
        logger.error(f"Error listing mappings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@project_router.get("/mappings/{mapping_id}", response_model=StandardResponse[DatasetMappingResponse])
async def get_mapping(
    mapping_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据 UUID 查询单个映射关系
    """
    try:
        service = DatasetMappingService(db)
        
        logger.info(f"Get mapping: {mapping_id}")
        
        mapping = await service.get_mapping_by_uuid(mapping_id)
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {mapping_id}"
            )
        
        logger.info(f"Found mapping: {mapping.mapping_id}")
        
        return StandardResponse(
            code=200,
            message="success",
            data=mapping
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mapping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@project_router.get("/mappings/by-source/{source_dataset_id}", response_model=StandardResponse[PaginatedData[DatasetMappingResponse]])
async def get_mappings_by_source(
    source_dataset_id: str,
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据源数据集 ID 查询所有映射关系（分页）
    
    返回该数据集创建的所有标注项目（不包括已删除的），支持分页查询
    """
    try:
        service = DatasetMappingService(db)
        
        # 计算 skip
        skip = (page - 1) * page_size
        
        logger.info(f"Get mappings by source dataset id: {source_dataset_id}, page={page}, page_size={page_size}")
        
        # 获取数据和总数
        mappings, total = await service.get_mappings_by_source_with_count(
            source_dataset_id=source_dataset_id,
            skip=skip,
            limit=page_size
        )
        
        # 计算总页数
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # 构造分页响应
        paginated_data = PaginatedData(
            page=page,
            size=page_size,
            total_elements=total,
            total_pages=total_pages,
            content=mappings
        )
        
        logger.info(f"Found {len(mappings)} mappings on page {page}, total: {total}")
        
        return StandardResponse(
            code=200,
            message="success",
            data=paginated_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mappings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
