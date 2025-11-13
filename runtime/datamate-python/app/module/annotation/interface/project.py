from typing import Optional
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import LabelingProject
from app.module.shared.schema import StandardResponse, PaginatedData
from app.module.dataset import DatasetManagementService
from app.core.logging import get_logger
from app.core.config import settings

from ..client import LabelStudioClient
from ..service.mapping import DatasetMappingService
from ..service.sync import SyncService
from ..service.template import AnnotationTemplateService
from ..schema import (
    DatasetMappingCreateRequest,
    DatasetMappingCreateResponse,
    DeleteDatasetResponse,
    DatasetMappingResponse,
)

router = APIRouter(
    prefix="/project",
    tags=["annotation/project"]
)
logger = get_logger(__name__)

@router.post("", response_model=StandardResponse[DatasetMappingCreateResponse], status_code=201)
async def create_mapping(
    request: DatasetMappingCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建数据集映射
    
    根据指定的DM程序中的数据集，创建Label Studio中的数据集，
    在数据库中记录这一关联关系，返回Label Studio数据集的ID
    
    注意：一个数据集可以创建多个标注项目
    
    支持通过 template_id 指定标注模板，如果提供了模板ID，则使用模板的配置
    """
    try:
        dm_client = DatasetManagementService(db)
        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        mapping_service = DatasetMappingService(db)
        sync_service = SyncService(dm_client, ls_client, mapping_service)
        template_service = AnnotationTemplateService()
        
        logger.info(f"Create dataset mapping request: {request.dataset_id}")
        
        # 从DM服务获取数据集信息
        dataset_info = await dm_client.get_dataset(request.dataset_id)
        if not dataset_info:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found in DM service: {request.dataset_id}"
            )
        
        project_name = request.name or \
                       dataset_info.name or \
                       "A new project from DataMate"
        
        project_description = request.description or \
                              dataset_info.description or \
                              f"Imported from DM dataset {dataset_info.name} ({dataset_info.id})"

        # 如果提供了模板ID，获取模板配置
        label_config = None
        if request.template_id:
            logger.info(f"Using template: {request.template_id}")
            template = await template_service.get_template(db, request.template_id)
            if not template:
                raise HTTPException(
                    status_code=404,
                    detail=f"Template not found: {request.template_id}"
                )
            label_config = template.label_config
            logger.debug(f"Template label config loaded for template: {template.name}")

        # 在Label Studio中创建项目
        project_data = await ls_client.create_project(
            title=project_name,
            description=project_description,
            label_config=label_config  # 传递模板配置
        )
        
        if not project_data:
            raise HTTPException(
                status_code=500,
                detail="Fail to create Label Studio project."
            )
        
        project_id = project_data["id"]
        
        # 配置本地存储：dataset/<id>
        local_storage_path = f"{settings.label_studio_local_document_root}/{request.dataset_id}"
        storage_result = await ls_client.create_local_storage(
            project_id=project_id,
            path=local_storage_path,
            title="Dataset_BLOB",
            use_blob_urls=True,
            description=f"Local storage for dataset {dataset_info.name}"
        )
        
        if not storage_result:
            # 本地存储配置失败，记录警告但不中断流程
            logger.warning(f"Failed to configure local storage for project {project_id}")
        else:
            logger.info(f"Local storage configured for project {project_id}: {local_storage_path}")

        labeling_project = LabelingProject(
                id=str(uuid.uuid4()),  # Generate UUID here
                dataset_id=request.dataset_id,
                labeling_project_id=str(project_id),
                name=project_name,
                template_id=request.template_id,  # Save template_id to database
            )

        # 创建映射关系，包含项目名称（先持久化映射以获得 mapping.id）
        mapping = await mapping_service.create_mapping(labeling_project)
        
        # 进行一次同步，使用创建后的 mapping.id
        await sync_service.sync_dataset_files(mapping.id, 100)
        
        response_data = DatasetMappingCreateResponse(
            id=mapping.id,
            labeling_project_id=str(mapping.labeling_project_id),
            labeling_project_name=mapping.name or project_name
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
    
@router.get("", response_model=StandardResponse[PaginatedData[DatasetMappingResponse]])
async def list_mappings(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数", alias="pageSize"),
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
        
        logger.info(f"List mappings: page={page}, returned {len(mappings)}/{total}")
        
        return StandardResponse(
            code=200,
            message="success",
            data=paginated_data
        )
        
    except Exception as e:
        logger.error(f"Error listing mappings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{mapping_id}", response_model=StandardResponse[DatasetMappingResponse])
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
        
        logger.info(f"Found mapping: {mapping.id}")
        
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

@router.get("/by-source/{dataset_id}", response_model=StandardResponse[PaginatedData[DatasetMappingResponse]])
async def get_mappings_by_source(
    dataset_id: str,
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数", alias="pageSize"),
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
        
        logger.info(f"Get mappings by source dataset id: {dataset_id}, page={page}, page_size={page_size}")
        
        # 获取数据和总数
        mappings, total = await service.get_mappings_by_source_with_count(
            dataset_id=dataset_id,
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

@router.delete("/{project_id}", response_model=StandardResponse[DeleteDatasetResponse])
async def delete_mapping(
    project_id: str = Path(..., description="映射UUID（path param）"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除映射关系和对应的 Label Studio 项目

    通过 path 参数 `project_id` 指定要删除的映射（映射的 UUID）。

    此操作会：
    1. 删除 Label Studio 中的项目
    2. 软删除数据库中的映射记录
    """
    try:
        logger.debug(f"Delete mapping request received: project_id={project_id!r}")

        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        service = DatasetMappingService(db)
        
        # 使用 mapping UUID 查询映射记录
        logger.debug(f"Deleting by mapping UUID: {project_id}")
        mapping = await service.get_mapping_by_uuid(project_id)

        logger.debug(f"Mapping lookup result: {mapping}")
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping either not found or not specified."
            )
        
        id = mapping.id
        labeling_project_id = mapping.labeling_project_id

        logger.debug(f"Found mapping: {id}, Label Studio project ID: {labeling_project_id}")
        
        # 1. 删除 Label Studio 项目
        try:
            logger.debug(f"Deleting Label Studio project: {labeling_project_id}")
            delete_success = await ls_client.delete_project(int(labeling_project_id))
            if delete_success:
                logger.debug(f"Successfully deleted Label Studio project: {labeling_project_id}")
            else:
                logger.warning(f"Failed to delete Label Studio project or project not found: {labeling_project_id}")
        except Exception as e:
            logger.error(f"Error deleting Label Studio project: {e}")
            # 继续执行，即使 Label Studio 项目删除失败也要删除映射记录
        
        # 2. 软删除映射记录
        soft_delete_success = await service.soft_delete_mapping(id)
        logger.debug(f"Soft delete result for mapping {id}: {soft_delete_success}")
        
        if not soft_delete_success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete mapping record"
            )

        logger.info(f"Successfully deleted mapping: {id}, Label Studio project: {labeling_project_id}")

        return StandardResponse(
            code=200,
            message="success",
            data=DeleteDatasetResponse(
                id=id,
                status="success"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mapping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
