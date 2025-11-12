from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from sqlalchemy.orm import aliased
from typing import Optional, List, Tuple
from datetime import datetime
import uuid

from app.core.logging import get_logger
from app.db.models import LabelingProject
from app.db.models.dataset_management import Dataset
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
    
    def _build_query_with_dataset_name(self):
        """Build base query with dataset name joined"""
        return select(
            LabelingProject,
            Dataset.name.label('dataset_name')
        ).outerjoin(
            Dataset,
            LabelingProject.dataset_id == Dataset.id
        )
    
    def _to_response_from_row(self, row) -> DatasetMappingResponse:
        """Convert query row (mapping + dataset_name) to response"""
        mapping = row[0]  # LabelingProject object
        dataset_name = row[1]  # dataset_name from join
        
        response_data = {
            "id": mapping.id,
            "dataset_id": mapping.dataset_id,
            "dataset_name": dataset_name,
            "labeling_project_id": mapping.labeling_project_id,
            "name": mapping.name,
            "description": getattr(mapping, 'description', None),
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at,
            "deleted_at": mapping.deleted_at,
        }
        
        return DatasetMappingResponse(**response_data)
    
    async def _to_response(self, mapping: LabelingProject) -> DatasetMappingResponse:
        """Convert ORM model to response with dataset name (for single entity operations)"""
        # Fetch dataset name
        dataset_name = None
        dataset_id = getattr(mapping, 'dataset_id', None)
        if dataset_id:
            dataset_result = await self.db.execute(
                select(Dataset.name).where(Dataset.id == dataset_id)
            )
            dataset_name = dataset_result.scalar_one_or_none()
        
        # Create response dict with all fields
        response_data = {
            "id": mapping.id,
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "labeling_project_id": mapping.labeling_project_id,
            "name": mapping.name,
            "description": getattr(mapping, 'description', None),
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at,
            "deleted_at": mapping.deleted_at,
        }
        
        return DatasetMappingResponse(**response_data)
    
    async def create_mapping(
        self, 
        labeling_project: LabelingProject
    ) -> DatasetMappingResponse:
        """创建数据集映射"""
        logger.info(f"Create dataset mapping: {labeling_project.dataset_id} -> {labeling_project.labeling_project_id}")
        
        # Use the passed object directly
        self.db.add(labeling_project)
        await self.db.commit()
        await self.db.refresh(labeling_project)
        
        logger.debug(f"Mapping created: {labeling_project.id}")
        return await self._to_response(labeling_project)
    
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
            return await self._to_response(mapping)
        
        logger.debug(f"No mapping found for source dataset id: {dataset_id}")
        return None
    
    async def get_mappings_by_dataset_id(
        self, 
        dataset_id: str,
        include_deleted: bool = False
    ) -> List[DatasetMappingResponse]:
        """根据源数据集ID获取所有映射关系"""
        logger.debug(f"Get all mappings by source dataset id: {dataset_id}")
        
        query = self._build_query_with_dataset_name().where(
            LabelingProject.dataset_id == dataset_id
        )
        
        if not include_deleted:
            query = query.where(LabelingProject.deleted_at.is_(None))
        
        result = await self.db.execute(
            query.order_by(LabelingProject.created_at.desc())
        )
        rows = result.all()
        
        logger.debug(f"Found {len(rows)} mappings")
        return [self._to_response_from_row(row) for row in rows]
    
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
            logger.debug(f"Found mapping: {mapping.id}")
            return await self._to_response(mapping)
        
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
            return await self._to_response(mapping)
        
        logger.debug(f"No mapping found for mapping id: {mapping_id}")
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
        
        query = self._build_query_with_dataset_name().where(
            LabelingProject.deleted_at.is_(None)
        )
        
        result = await self.db.execute(
            query
            .offset(skip)
            .limit(limit)
            .order_by(LabelingProject.created_at.desc())
        )
        rows = result.all()
        
        logger.debug(f"Found {len(rows)} mappings")
        return [self._to_response_from_row(row) for row in rows]
    
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
        query = self._build_query_with_dataset_name()
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
        rows = result.all()
        
        logger.debug(f"Found {len(rows)} mappings, total: {total}")
        return [self._to_response_from_row(row) for row in rows], total
    
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
        query = self._build_query_with_dataset_name().where(
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
        rows = result.all()
        
        logger.debug(f"Found {len(rows)} mappings, total: {total}")
        return [self._to_response_from_row(row) for row in rows], total