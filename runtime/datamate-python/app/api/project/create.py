from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.services.dataset_mapping_service import DatasetMappingService
from app.infrastructure import DatamateClient, LabelStudioClient
from app.schemas.dataset_mapping import (
    DatasetMappingCreateRequest,
    DatasetMappingCreateResponse,
)
from app.schemas import StandardResponse
from app.core.logging import get_logger
from app.core.config import settings
from . import project_router

logger = get_logger(__name__)

@project_router.post("/create", response_model=StandardResponse[DatasetMappingCreateResponse], status_code=201)
async def create_dataset_mapping(
    request: DatasetMappingCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建数据集映射
    
    根据指定的DM程序中的数据集，创建Label Studio中的数据集，
    在数据库中记录这一关联关系，返回Label Studio数据集的ID
    
    注意：一个数据集可以创建多个标注项目
    """
    try:
        dm_client = DatamateClient(db)
        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        service = DatasetMappingService(db)
        
        logger.info(f"Create dataset mapping request: {request.dataset_id}")
        
        # 从DM服务获取数据集信息
        dataset_info = await dm_client.get_dataset(request.dataset_id)
        if not dataset_info:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found in DM service: {request.dataset_id}"
            )
        
        # 确定数据类型（基于数据集类型）
        data_type = "image"  # 默认值
        if dataset_info.type and dataset_info.type.code:
            type_code = dataset_info.type.code.lower()
            if "audio" in type_code:
                data_type = "audio"
            elif "video" in type_code:
                data_type = "video"
            elif "text" in type_code:
                data_type = "text"
        
        project_name = f"{dataset_info.name}"
        
        # 在Label Studio中创建项目
        project_data = await ls_client.create_project(
            title=project_name,
            description=dataset_info.description or f"Imported from DM dataset {dataset_info.id}",
            data_type=data_type
        )
        
        if not project_data:
            raise HTTPException(
                status_code=500,
                detail="Fail to create Label Studio project."
            )
        
        project_id = project_data["id"]
        
        # 配置本地存储：dataset/<id>
        local_storage_path = f"{settings.label_studio_local_storage_dataset_base_path}/{request.dataset_id}"
        storage_result = await ls_client.create_local_storage(
            project_id=project_id,
            path=local_storage_path,
            title="Dataset_BLOB",
            use_blob_urls=True,
            description=f"Local storage for dataset {dataset_info.name}"
        )

        # 配置本地存储：upload
        local_storage_path = f"{settings.label_studio_local_storage_upload_base_path}"
        storage_result = await ls_client.create_local_storage(
            project_id=project_id,
            path=local_storage_path,
            title="Upload_BLOB",
            use_blob_urls=True,
            description=f"Local storage for dataset {dataset_info.name}"
        )
        
        if not storage_result:
            # 本地存储配置失败，记录警告但不中断流程
            logger.warning(f"Failed to configure local storage for project {project_id}")
        else:
            logger.info(f"Local storage configured for project {project_id}: {local_storage_path}")
        
        # 创建映射关系，包含项目名称
        mapping = await service.create_mapping(
            request, 
            str(project_id),
            project_name
        )
        
        logger.debug(
            f"Dataset mapping created: {mapping.mapping_id} -> S {mapping.dataset_id} <> L {mapping.labelling_project_id}"
        )
        
        response_data = DatasetMappingCreateResponse(
            mapping_id=mapping.mapping_id,
            labelling_project_id=mapping.labelling_project_id,
            labelling_project_name=mapping.labelling_project_name or project_name,
            message="Dataset mapping created successfully"
        )
        
        return StandardResponse(
            code=201,
            message="success",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while creating dataset mapping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")