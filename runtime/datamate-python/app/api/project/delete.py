from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.services.dataset_mapping_service import DatasetMappingService
from app.infrastructure import DatamateClient, LabelStudioClient
from app.schemas.dataset_mapping import DeleteDatasetResponse
from app.schemas import StandardResponse
from app.core.logging import get_logger
from app.core.config import settings

from . import project_router

logger = get_logger(__name__)

@project_router.delete("/mappings", response_model=StandardResponse[DeleteDatasetResponse])
async def delete_mapping(
    m: Optional[str] = Query(None, description="映射UUID"),
    proj: Optional[str] = Query(None, description="Label Studio项目ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除映射关系和对应的 Label Studio 项目
    
    可以通过以下任一方式指定要删除的映射：
    - m: 映射UUID
    - proj: Label Studio项目ID
    - 两者都提供（优先使用 m）
    
    此操作会：
    1. 删除 Label Studio 中的项目
    2. 软删除数据库中的映射记录
    """
    try:
        # 至少需要提供一个参数
        if not m and not proj:
            raise HTTPException(
                status_code=400,
                detail="Either 'm' (mapping UUID) or 'proj' (project ID) must be provided"
            )

        ls_client = LabelStudioClient(base_url=settings.label_studio_base_url,
                                      token=settings.label_studio_user_token)
        service = DatasetMappingService(db)
        
        # 优先使用 mapping_id 查询
        if m:
            logger.debug(f"Deleting by mapping UUID: {m}")
            mapping = await service.get_mapping_by_uuid(m)
        # 如果没有提供 m，使用 proj 查询
        elif proj:
            logger.debug(f"Deleting by project ID: {proj}")
            mapping = await service.get_mapping_by_labelling_project_id(proj)
        else:
            mapping = None
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping either not found or not specified."
            )
        
        mapping_id = mapping.mapping_id
        labelling_project_id = mapping.labelling_project_id
        labelling_project_name = mapping.labelling_project_name
        
        logger.debug(f"Found mapping: {mapping_id}, Label Studio project ID: {labelling_project_id}")
        
        # 1. 删除 Label Studio 项目
        try:
            delete_success = await ls_client.delete_project(int(labelling_project_id))
            if delete_success:
                logger.debug(f"Successfully deleted Label Studio project: {labelling_project_id}")
            else:
                logger.warning(f"Failed to delete Label Studio project or project not found: {labelling_project_id}")
        except Exception as e:
            logger.error(f"Error deleting Label Studio project: {e}")
            # 继续执行，即使 Label Studio 项目删除失败也要删除映射记录
        
        # 2. 软删除映射记录
        soft_delete_success = await service.soft_delete_mapping(mapping_id)
        
        if not soft_delete_success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete mapping record"
            )

        logger.info(f"Successfully deleted mapping: {mapping_id}, Label Studio project: {labelling_project_id}")

        return StandardResponse(
            code=200,
            message="success",
            data=DeleteDatasetResponse(
                mapping_id=mapping_id,
                status="success",
                message=f"Successfully deleted mapping and Label Studio project '{labelling_project_name}'"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mapping: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
