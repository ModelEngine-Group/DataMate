from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.database import get_db
from app.services.dataset_mapping_service import DatasetMappingService
from app.services.sync_service import SyncService
from app.clients import get_clients
from app.exceptions import NoDatasetInfoFoundError, DatasetMappingNotFoundError
from app.schemas.dataset_mapping import (
    DatasetMappingResponse,
    SyncDatasetRequest,
    SyncDatasetResponse,
)
from app.schemas import StandardResponse
from app.core.logging import get_logger
from . import project_router

logger = get_logger(__name__)

@project_router.post("/sync", response_model=StandardResponse[SyncDatasetResponse])
async def sync_dataset_content(
    request: SyncDatasetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    同步数据集内容
    
    根据指定的mapping ID，同步DM程序数据集中的内容到Label Studio数据集中，
    在数据库中记录更新时间，返回更新状态
    """
    try:
        dm_client_instance, ls_client_instance = get_clients()
        mapping_service = DatasetMappingService(db)
        sync_service = SyncService(dm_client_instance, ls_client_instance, mapping_service)
        
        logger.info(f"Sync dataset content request: mapping_id={request.mapping_id}")
        
        # 根据 mapping_id 获取映射关系
        mapping = await mapping_service.get_mapping_by_uuid(request.mapping_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {request.mapping_id}"
            )
        
        # 执行同步（使用映射中的源数据集UUID）
        result = await sync_service.sync_dataset_files(request.mapping_id, request.batch_size)
        
        logger.info(f"Sync completed: {result.synced_files}/{result.total_files} files")
        
        return StandardResponse(
            code=200,
            message="success",
            data=result
        )
        
    except HTTPException:
        raise
    except NoDatasetInfoFoundError as e:
        logger.error(f"Failed to get dataset info: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except DatasetMappingNotFoundError as e:
        logger.error(f"Mapping not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing dataset content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")