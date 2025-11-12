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
    SyncAnnotationsRequest,
    SyncAnnotationsResponse,
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
    同步数据集内容（包括文件和标注）
    
    根据指定的mapping ID，同步DM程序数据集中的内容到Label Studio数据集中。
    默认同时同步文件和标注数据。
    
    Args:
        request: 同步请求，包含:
            - id: 映射ID（mapping UUID）
            - batchSize: 批处理大小
            - filePriority: 文件同步优先级
            - labelPriority: 标签同步优先级
            - syncAnnotations: 是否同步标注（默认True）
            - annotationDirection: 标注同步方向（默认bidirectional）
            - overwrite: 是否允许覆盖DataMate中的标注（默认True）
            - overwriteLabelingProject: 是否允许覆盖Label Studio中的标注（默认True）
    
    Returns:
        同步结果
    """
    try:
        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        dm_client = DatasetManagementService(db)
        mapping_service = DatasetMappingService(db)
        sync_service = SyncService(dm_client, ls_client, mapping_service)

        logger.debug(f"Sync dataset content request: mapping_id={request.id}, sync_annotations={request.sync_annotations}")

        # request.id validation
        mapping = await mapping_service.get_mapping_by_uuid(request.id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {request.id}"
            )
        
        # Sync dataset files
        result = await sync_service.sync_dataset_files(request.id, request.batch_size)
        
        # Sync annotations if requested
        if request.sync_annotations:
            logger.info(f"Syncing annotations: direction={request.annotation_direction}")
            
            # 根据方向执行标注同步
            if request.annotation_direction == "ls_to_dm":
                await sync_service.sync_annotations_from_ls_to_dm(
                    mapping,
                    request.batch_size,
                    request.overwrite
                )
            elif request.annotation_direction == "dm_to_ls":
                await sync_service.sync_annotations_from_dm_to_ls(
                    mapping,
                    request.batch_size,
                    request.overwrite_labeling_project
                )
            elif request.annotation_direction == "bidirectional":
                await sync_service.sync_annotations_bidirectional(
                    mapping,
                    request.batch_size,
                    request.overwrite,
                    request.overwrite_labeling_project
                )
        
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


@router.post("/annotation/sync", response_model=StandardResponse[SyncAnnotationsResponse])
async def sync_annotations(
    request: SyncAnnotationsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    仅同步标注结果（支持双向同步）
    
    根据指定的mapping ID和同步方向，在DM数据集和Label Studio之间同步标注结果。
    标注结果存储在数据集文件表的tags字段中，使用简化格式。
    
    同步策略：
    - 默认为双向同步，基于时间戳自动解决冲突
    - overwrite: 控制是否允许用Label Studio的标注覆盖DataMate（基于时间戳比较）
    - overwriteLabelingProject: 控制是否允许用DataMate的标注覆盖Label Studio（基于时间戳比较）
    - 如果Label Studio标注的updated_at更新，且overwrite=True，则覆盖DataMate
    - 如果DataMate标注的updated_at更新，且overwriteLabelingProject=True，则覆盖Label Studio
    
    Args:
        request: 同步请求，包含:
            - id: 映射ID（mapping UUID）
            - batchSize: 批处理大小
            - direction: 同步方向 (ls_to_dm/dm_to_ls/bidirectional)
            - overwrite: 是否允许覆盖DataMate中的标注（默认True）
            - overwriteLabelingProject: 是否允许覆盖Label Studio中的标注（默认True）
    
    Returns:
        同步结果，包含同步统计信息和冲突解决情况
    """
    try:
        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        dm_client = DatasetManagementService(db)
        mapping_service = DatasetMappingService(db)
        sync_service = SyncService(dm_client, ls_client, mapping_service)

        logger.info(f"Sync annotations request: mapping_id={request.id}, direction={request.direction}, overwrite={request.overwrite}, overwrite_ls={request.overwrite_labeling_project}")

        # 验证映射是否存在
        mapping = await mapping_service.get_mapping_by_uuid(request.id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping not found: {request.id}"
            )
        
        # 根据方向执行同步
        if request.direction == "ls_to_dm":
            result = await sync_service.sync_annotations_from_ls_to_dm(
                mapping,
                request.batch_size,
                request.overwrite
            )
        elif request.direction == "dm_to_ls":
            result = await sync_service.sync_annotations_from_dm_to_ls(
                mapping,
                request.batch_size,
                request.overwrite_labeling_project
            )
        elif request.direction == "bidirectional":
            result = await sync_service.sync_annotations_bidirectional(
                mapping,
                request.batch_size,
                request.overwrite,
                request.overwrite_labeling_project
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid direction: {request.direction}"
            )
        
        logger.info(f"Annotation sync completed: synced_to_dm={result.synced_to_dm}, synced_to_ls={result.synced_to_ls}, conflicts_resolved={result.conflicts_resolved}")
        
        return StandardResponse(
            code=200,
            message="success",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing annotations: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/check-ls-connection")
async def check_label_studio_connection():
    """
    检查Label Studio连接状态
    
    用于诊断Label Studio连接问题，返回连接状态和配置信息
    """
    try:
        ls_client = LabelStudioClient(
            base_url=settings.label_studio_base_url,
            token=settings.label_studio_user_token
        )
        
        # 尝试获取项目列表来测试连接
        try:
            response = await ls_client.client.get("/api/projects")
            response.raise_for_status()
            projects = response.json()
            
            token_display = settings.label_studio_user_token[:10] + "..." if settings.label_studio_user_token else "None"
            
            return StandardResponse(
                code=200,
                message="success",
                data={
                    "status": "connected",
                    "base_url": settings.label_studio_base_url,
                    "token": token_display,
                    "projects_count": len(projects.get("results", [])) if isinstance(projects, dict) else len(projects),
                    "message": "Successfully connected to Label Studio"
                }
            )
        except Exception as e:
            token_display = settings.label_studio_user_token[:10] + "..." if settings.label_studio_user_token else "None"
            
            return StandardResponse(
                code=500,
                message="error",
                data={
                    "status": "disconnected",
                    "base_url": settings.label_studio_base_url,
                    "token": token_display,
                    "error": str(e),
                    "message": f"Failed to connect to Label Studio: {str(e)}",
                    "troubleshooting": [
                        "1. Check if Label Studio is running: docker ps | grep label-studio",
                        "2. Verify LABEL_STUDIO_BASE_URL in .env file",
                        "3. Verify LABEL_STUDIO_USER_TOKEN is valid",
                        "4. Check network connectivity between services"
                    ]
                }
            )
    except Exception as e:
        logger.error(f"Error checking Label Studio connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))