from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.module.shared.schema import StandardResponse
from app.module.dataset import DatasetManagementService
from app.core.logging import get_logger
from app.core.config import settings
from app.exception import NoDatasetInfoFoundError, DatasetMappingNotFoundError

from ..client import LabelStudioClient
from ..service.sync import SyncService
from ..service.mapping import DatasetMappingService
from ..schema import (
    SyncDatasetRequest,
    SyncDatasetResponse,
)


router = APIRouter(
    prefix="/task",
    tags=["annotation/task"]
)
logger = get_logger(__name__)

@router.post("/sync", response_model=StandardResponse[SyncDatasetResponse])
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
        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        dm_client = DatasetManagementService(db)
        mapping_service = DatasetMappingService(db)
        sync_service = SyncService(dm_client, ls_client, mapping_service)

        logger.info(f"Sync dataset content request: mapping_id={request.id}")

        # request.id 合法性校验
        mapping = await mapping_service.get_mapping_by_uuid(request.id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {request.id}"
            )
        
        # 执行同步（使用映射中的源数据集UUID）
        result = await sync_service.sync_dataset_files(request.id, request.batch_size)
        
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