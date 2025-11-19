from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

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
    UpdateFileTagsRequest,
    UpdateFileTagsResponse,
    UpdateFileTagsRequest,
    UpdateFileTagsResponse
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
    Sync Dataset Content (Files and Annotations)
    
    根据指定的mapping ID，同步DM程序数据集中的内容到Label Studio数据集中。
    默认同时同步文件和标注数据。
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
    Sync Annotations Only (Bidirectional Support)

    同步指定 mapping 下的标注数据，支持单向或双向同步，基于时间戳自动解决冲突。
    请求与响应由 Pydantic 模型 `SyncAnnotationsRequest` / `SyncAnnotationsResponse` 定义。
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
    Check Label Studio Connection Status

    诊断 Label Studio 连接并返回简要连接信息（状态、base URL、token 摘要、项目统计）。
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

@router.put(
    "/{file_id}",
    response_model=StandardResponse[UpdateFileTagsResponse],
)
async def update_file_tags(
    request: UpdateFileTagsRequest,
    file_id: str = Path(..., description="文件ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update File Tags (Partial Update with Auto Format Conversion)

    接收部分标签更新并合并到指定文件（只修改提交的标签，其余保持不变），并更新 `tags_updated_at`。
    
    支持两种标签格式：
    1. 简化格式（外部用户提交）:
       [{"from_name": "label", "to_name": "image", "values": ["cat", "dog"]}]
    
    2. 完整格式（内部存储）:
       [{"id": "...", "from_name": "label", "to_name": "image", "type": "choices", 
         "value": {"choices": ["cat", "dog"]}}]
    
    系统会自动根据数据集关联的模板将简化格式转换为完整格式。
    请求与响应使用 Pydantic 模型 `UpdateFileTagsRequest` / `UpdateFileTagsResponse`。
    """
    service = DatasetManagementService(db)
    
    # 首先获取文件所属的数据集
    from sqlalchemy.future import select
    from app.db.models import DatasetFiles
    
    result = await db.execute(
        select(DatasetFiles).where(DatasetFiles.id == file_id)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    
    dataset_id = str(file_record.dataset_id)  # type: ignore - Convert Column to str
    
    # 查找数据集关联的模板ID
    from ..service.mapping import DatasetMappingService
    
    mapping_service = DatasetMappingService(db)
    template_id = await mapping_service.get_template_id_by_dataset_id(dataset_id)
    
    if template_id:
        logger.info(f"Found template {template_id} for dataset {dataset_id}, will auto-convert tag format")
    else:
        logger.warning(f"No template found for dataset {dataset_id}, tags must be in full format")
    
    # 更新标签（如果有模板ID则自动转换格式）
    success, error_msg, updated_at = await service.update_file_tags_partial(
        file_id=file_id,
        new_tags=request.tags,
        template_id=template_id  # 传递模板ID以启用自动转换
    )
    
    if not success:
        if "not found" in (error_msg or "").lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg or "更新标签失败")
    
    # 重新获取更新后的文件记录（获取完整标签列表）
    result = await db.execute(
        select(DatasetFiles).where(DatasetFiles.id == file_id)
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    
    response_data = UpdateFileTagsResponse(
        fileId=file_id,
        tags=file_record.tags or [],  # type: ignore
        tagsUpdatedAt=updated_at or datetime.now()
    )
    
    return StandardResponse(
        code=200,
        message="标签更新成功",
        data=response_data
    )
