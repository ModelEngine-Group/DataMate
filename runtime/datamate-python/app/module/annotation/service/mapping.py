from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from typing import Optional, List, Tuple
from datetime import datetime
import uuid

from app.core.logging import get_logger
from app.db.models import LabelingProject
from app.module.annotation.schema import (
    DatasetMappingCreateRequest, 
    DatasetMappingUpdateRequest, 
    DatasetMappingResponse
)

logger = get_logger(__name__)

class DatasetMappingService:
    """数据集映射服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_mapping(
        self, 
        labeling_project: LabelingProject
    ) -> DatasetMappingResponse:
        """创建数据集映射"""
        logger.info(f"Create dataset mapping: {labeling_project.dataset_id} -> {labeling_project.labeling_project_id}")
        
        db_mapping = LabelingProject(
            id=str(uuid.uuid4()),
            dataset_id=labeling_project.dataset_id,
            labeling_project_id=labeling_project.labeling_project_id,
            name=labeling_project.name
        )

        self.db.add(db_mapping)
        await self.db.commit()
        await self.db.refresh(db_mapping)
        
        logger.debug(f"Mapping created: {db_mapping.id}")
        return DatasetMappingResponse.model_validate(db_mapping)
    
    async def get_mapping_by_source_uuid(
        self, 
        dataset_id: str
    ) -> Optional[DatasetMappingResponse]:
        """根据源数据集ID获取映射（返回第一个未删除的）"""
        logger.debug(f"Get mapping by source dataset id: {dataset_id}")
        
        result = await self.db.execute(
            select(LabelingProject).where(
                LabelingProject.dataset_id == dataset_id,
                LabelingProject.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.id}")
            return DatasetMappingResponse.model_validate(mapping)
        
        logger.debug(f"No mapping found for source dataset id: {dataset_id}")
        return None
    
    async def get_mappings_by_dataset_id(
        self, 
        dataset_id: str,
        include_deleted: bool = False
    ) -> List[DatasetMappingResponse]:
        """根据源数据集ID获取所有映射关系"""
        logger.debug(f"Get all mappings by source dataset id: {dataset_id}")
        
        query = select(LabelingProject).where(
            LabelingProject.dataset_id == dataset_id
        )
        
        if not include_deleted:
            query = query.where(LabelingProject.deleted_at.is_(None))
        
        result = await self.db.execute(
            query.order_by(LabelingProject.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings]
    
    async def get_mapping_by_labeling_project_id(
        self, 
        labeling_project_id: str
    ) -> Optional[DatasetMappingResponse]:
        """根据Label Studio项目ID获取映射"""
        logger.debug(f"Get mapping by Label Studio project id: {labeling_project_id}")
        
        result = await self.db.execute(
            select(LabelingProject).where(
                LabelingProject.labeling_project_id == labeling_project_id,
                LabelingProject.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.mapping_id}")
            return DatasetMappingResponse.model_validate(mapping)
        
        logger.debug(f"No mapping found for Label Studio project id: {labeling_project_id}")
        return None
    
    async def get_mapping_by_uuid(self, mapping_id: str) -> Optional[DatasetMappingResponse]:
        """根据映射UUID获取映射"""
        logger.debug(f"Get mapping: {mapping_id}")
        
        result = await self.db.execute(
            select(LabelingProject).where(
                LabelingProject.id == mapping_id,
                LabelingProject.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.id}")
            return DatasetMappingResponse.model_validate(mapping)
        
        logger.debug(f"Mapping not found: {mapping_id}")
        return None
    
    async def update_mapping(
        self, 
        mapping_id: str, 
        update_data: DatasetMappingUpdateRequest
    ) -> Optional[DatasetMappingResponse]:
        """更新映射信息"""
        logger.info(f"Update mapping: {mapping_id}")
        
        mapping = await self.get_mapping_by_uuid(mapping_id)
        if not mapping:
            return None
        
        update_values = update_data.model_dump(exclude_unset=True)
        update_values["last_updated_at"] = datetime.now()
        
        result = await self.db.execute(
            update(LabelingProject)
            .where(LabelingProject.id == mapping_id)
            .values(**update_values)
        )
        await self.db.commit()
        
        if result.rowcount > 0:
            return await self.get_mapping_by_uuid(mapping_id)
        return None
    
    async def soft_delete_mapping(self, mapping_id: str) -> bool:
        """软删除映射"""
        logger.info(f"Soft delete mapping: {mapping_id}")
        
        result = await self.db.execute(
            update(LabelingProject)
            .where(
                LabelingProject.id == mapping_id,
                LabelingProject.deleted_at.is_(None)
            )
            .values(deleted_at=datetime.now())
        )
        await self.db.commit()
        
        success = result.rowcount > 0
        if success:
            logger.info(f"Mapping soft-deleted: {mapping_id}")
        else:
            logger.warning(f"Mapping not exists or already deleted: {mapping_id}")
        
        return success
    
    async def get_all_mappings(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DatasetMappingResponse]:
        """获取所有有效映射"""
        logger.debug(f"List all mappings, skip: {skip}, limit: {limit}")
        
        result = await self.db.execute(
            select(LabelingProject)
            .where(LabelingProject.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(LabelingProject.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings]
    
    async def count_mappings(self, include_deleted: bool = False) -> int:
        """统计映射总数"""
        query = select(func.count()).select_from(LabelingProject)
        
        if not include_deleted:
            query = query.where(LabelingProject.deleted_at.is_(None))
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def get_all_mappings_with_count(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[DatasetMappingResponse], int]:
        """获取所有映射及总数（用于分页）"""
        logger.debug(f"List all mappings with count, skip: {skip}, limit: {limit}")
        
        # 构建查询
        query = select(LabelingProject)
        if not include_deleted:
            query = query.where(LabelingProject.deleted_at.is_(None))
        
        # 获取总数
        count_query = select(func.count()).select_from(LabelingProject)
        if not include_deleted:
            count_query = count_query.where(LabelingProject.deleted_at.is_(None))
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        # 获取数据
        result = await self.db.execute(
            query
            .offset(skip)
            .limit(limit)
            .order_by(LabelingProject.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings, total: {total}")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings], total
    
    async def get_mappings_by_source_with_count(
        self,
        dataset_id: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> Tuple[List[DatasetMappingResponse], int]:
        """根据源数据集ID获取映射关系及总数（用于分页）"""
        logger.debug(f"Get mappings by source dataset id with count: {dataset_id}")
        
        # 构建查询
        query = select(LabelingProject).where(
            LabelingProject.dataset_id == dataset_id
        )
        
        if not include_deleted:
            query = query.where(LabelingProject.deleted_at.is_(None))
        
        # 获取总数
        count_query = select(func.count()).select_from(LabelingProject).where(
            LabelingProject.dataset_id == dataset_id
        )
        if not include_deleted:
            count_query = count_query.where(LabelingProject.deleted_at.is_(None))
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        # 获取数据
        result = await self.db.execute(
            query
            .offset(skip)
            .limit(limit)
            .order_by(LabelingProject.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings, total: {total}")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings], total