from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.dataset_mapping import DatasetMapping
from app.schemas.dataset_mapping import (
    DatasetMappingCreateRequest, 
    DatasetMappingUpdateRequest, 
    DatasetMappingResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

class DatasetMappingService:
    """数据集映射服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_mapping(
        self, 
        mapping_data: DatasetMappingCreateRequest, 
        labelling_project_id: str,
        labelling_project_name: str
    ) -> DatasetMappingResponse:
        """创建数据集映射"""
        logger.info(f"Create dataset mapping: {mapping_data.source_dataset_id} -> {labelling_project_id}")
        
        db_mapping = DatasetMapping(
            mapping_id=str(uuid.uuid4()),
            source_dataset_id=mapping_data.source_dataset_id,
            labelling_project_id=labelling_project_id,
            labelling_project_name=labelling_project_name
        )
        
        self.db.add(db_mapping)
        await self.db.commit()
        await self.db.refresh(db_mapping)
        
        logger.info(f"Mapping created: {db_mapping.mapping_id}")
        return DatasetMappingResponse.model_validate(db_mapping)
    
    async def get_mapping_by_source_uuid(
        self, 
        source_dataset_id: str
    ) -> Optional[DatasetMappingResponse]:
        """根据源数据集ID获取映射（返回第一个未删除的）"""
        logger.debug(f"Get mapping by source dataset id: {source_dataset_id}")
        
        result = await self.db.execute(
            select(DatasetMapping).where(
                DatasetMapping.source_dataset_id == source_dataset_id,
                DatasetMapping.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.mapping_id}")
            return DatasetMappingResponse.model_validate(mapping)
        
        logger.debug(f"No mapping found for source dataset id: {source_dataset_id}")
        return None
    
    async def get_mappings_by_source_dataset_id(
        self, 
        source_dataset_id: str,
        include_deleted: bool = False
    ) -> List[DatasetMappingResponse]:
        """根据源数据集ID获取所有映射关系"""
        logger.debug(f"Get all mappings by source dataset id: {source_dataset_id}")
        
        query = select(DatasetMapping).where(
            DatasetMapping.source_dataset_id == source_dataset_id
        )
        
        if not include_deleted:
            query = query.where(DatasetMapping.deleted_at.is_(None))
        
        result = await self.db.execute(
            query.order_by(DatasetMapping.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings]
    
    async def get_mapping_by_labelling_project_id(
        self, 
        labelling_project_id: str
    ) -> Optional[DatasetMappingResponse]:
        """根据Label Studio项目ID获取映射"""
        logger.debug(f"Get mapping by Label Studio project id: {labelling_project_id}")
        
        result = await self.db.execute(
            select(DatasetMapping).where(
                DatasetMapping.labelling_project_id == labelling_project_id,
                DatasetMapping.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.mapping_id}")
            return DatasetMappingResponse.model_validate(mapping)
        
        logger.debug(f"No mapping found for Label Studio project id: {labelling_project_id}")
        return None
    
    async def get_mapping_by_uuid(self, mapping_id: str) -> Optional[DatasetMappingResponse]:
        """根据映射UUID获取映射"""
        logger.debug(f"Get mapping: {mapping_id}")
        
        result = await self.db.execute(
            select(DatasetMapping).where(
                DatasetMapping.mapping_id == mapping_id,
                DatasetMapping.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.mapping_id}")
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
        update_values["last_updated_at"] = datetime.utcnow()
        
        result = await self.db.execute(
            update(DatasetMapping)
            .where(DatasetMapping.mapping_id == mapping_id)
            .values(**update_values)
        )
        await self.db.commit()
        
        if result.rowcount > 0:
            return await self.get_mapping_by_uuid(mapping_id)
        return None
    
    async def update_last_updated_at(self, mapping_id: str) -> bool:
        """更新最后更新时间"""
        logger.debug(f"Update mapping last updated at: {mapping_id}")
        
        result = await self.db.execute(
            update(DatasetMapping)
            .where(
                DatasetMapping.mapping_id == mapping_id,
                DatasetMapping.deleted_at.is_(None)
            )
            .values(last_updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def soft_delete_mapping(self, mapping_id: str) -> bool:
        """软删除映射"""
        logger.info(f"Soft delete mapping: {mapping_id}")
        
        result = await self.db.execute(
            update(DatasetMapping)
            .where(
                DatasetMapping.mapping_id == mapping_id,
                DatasetMapping.deleted_at.is_(None)
            )
            .values(deleted_at=datetime.utcnow())
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
            select(DatasetMapping)
            .where(DatasetMapping.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(DatasetMapping.created_at.desc())
        )
        mappings = result.scalars().all()
        
        logger.debug(f"Found {len(mappings)} mappings")
        return [DatasetMappingResponse.model_validate(mapping) for mapping in mappings]
    
    async def count_mappings(self) -> int:
        """统计映射总数"""
        result = await self.db.execute(
            select(DatasetMapping)
            .where(DatasetMapping.deleted_at.is_(None))
        )
        mappings = result.scalars().all()
        return len(mappings)