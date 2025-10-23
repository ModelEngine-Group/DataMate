from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.services.dataset_mapping_service import DatasetMappingService
from app.schemas.dataset_mapping import DatasetMappingResponse
from app.schemas import StandardResponse
from app.core.logging import get_logger
from . import project_router

logger = get_logger(__name__)

@project_router.get("/mappings/list", response_model=StandardResponse[List[DatasetMappingResponse]])
async def list_mappings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    查询所有映射关系
    
    返回所有有效的数据集映射关系（未被软删除的）
    """
    try:
        service = DatasetMappingService(db)
        
        logger.info(f"Listing mappings, skip={skip}, limit={limit}")
        
        mappings = await service.get_all_mappings(skip=skip, limit=limit)
        
        logger.info(f"Found {len(mappings)} mappings")
        
        return StandardResponse(
            code=200,
            message="success",
            data=mappings
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


@project_router.get("/mappings/by-source/{source_dataset_id}", response_model=StandardResponse[List[DatasetMappingResponse]])
async def get_mappings_by_source(
    source_dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据源数据集 ID 查询所有映射关系
    
    返回该数据集创建的所有标注项目（包括已删除的）
    """
    try:
        service = DatasetMappingService(db)
        
        logger.info(f"Get mappings by source dataset id: {source_dataset_id}")
        
        mappings = await service.get_mappings_by_source_dataset_id(source_dataset_id)
        
        logger.info(f"Found {len(mappings)} mappings")
        
        return StandardResponse(
            code=200,
            message="success",
            data=mappings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mappings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
