from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from sqlalchemy.orm import aliased
from typing import Optional, List, Tuple
from datetime import datetime
import uuid

from app.core.logging import get_logger
from app.db.models import LabelingProject, AnnotationTemplate
from app.db.models.dataset_management import Dataset
from app.module.annotation.schema import (
    DatasetMappingCreateRequest, 
    DatasetMappingUpdateRequest, 
    DatasetMappingResponse,
    AnnotationTemplateResponse
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
    
    async def _to_response_from_row(
        self, 
        row, 
        include_template: bool = False
    ) -> DatasetMappingResponse:
        """
        Convert query row (mapping + dataset_name) to response
        
        Args:
            row: Query result row containing (LabelingProject, dataset_name)
            include_template: If True, fetch and include full template details
        """
        mapping = row[0]  # LabelingProject object
        dataset_name = row[1]  # dataset_name from join
        
        # Get template_id from mapping
        template_id = getattr(mapping, 'template_id', None)
        
        # Optionally fetch full template details
        template_response = None
        if include_template and template_id:
            from ..service.template import AnnotationTemplateService
            template_service = AnnotationTemplateService()
            template_response = await template_service.get_template(self.db, template_id)
            logger.debug(f"Included template details for template_id: {template_id}")
        
        response_data = {
            "id": mapping.id,
            "dataset_id": mapping.dataset_id,
            "dataset_name": dataset_name,
            "labeling_project_id": mapping.labeling_project_id,
            "name": mapping.name,
            "description": getattr(mapping, 'description', None),
            "template_id": template_id,
            "template": template_response,
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at,
            "deleted_at": mapping.deleted_at,
        }
        
        return DatasetMappingResponse(**response_data)
    
    async def _to_response(
        self, 
        mapping: LabelingProject, 
        include_template: bool = False
    ) -> DatasetMappingResponse:
        """
        Convert ORM model to response with dataset name (for single entity operations)
        
        Args:
            mapping: LabelingProject ORM object
            include_template: If True, fetch and include full template details
        """
        # Fetch dataset name
        dataset_name = None
        dataset_id = getattr(mapping, 'dataset_id', None)
        if dataset_id:
            dataset_result = await self.db.execute(
                select(Dataset.name).where(Dataset.id == dataset_id)
            )
            dataset_name = dataset_result.scalar_one_or_none()
        
        # Get template_id from mapping
        template_id = getattr(mapping, 'template_id', None)
        
        # Optionally fetch full template details
        template_response = None
        if include_template and template_id:
            from ..service.template import AnnotationTemplateService
            template_service = AnnotationTemplateService()
            template_response = await template_service.get_template(self.db, template_id)
            logger.debug(f"Included template details for template_id: {template_id}")
        
        # Create response dict with all fields
        response_data = {
            "id": mapping.id,
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "labeling_project_id": mapping.labeling_project_id,
            "name": mapping.name,
            "description": getattr(mapping, 'description', None),
            "template_id": template_id,
            "template": template_response,
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
        logger.debug(f"Create dataset mapping: {labeling_project.dataset_id} -> {labeling_project.labeling_project_id}")
        
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
        # Convert rows to responses (async comprehension)
        responses = []
        for row in rows:
            response = await self._to_response_from_row(row, include_template=False)
            responses.append(response)
        return responses
    
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
    
    async def get_mapping_by_uuid(
        self, 
        mapping_id: str, 
        include_template: bool = False
    ) -> Optional[DatasetMappingResponse]:
        """
        根据映射UUID获取映射
        
        Args:
            mapping_id: 映射UUID
            include_template: 是否包含完整的模板信息
        """
        logger.debug(f"Get mapping: {mapping_id}, include_template={include_template}")
        
        result = await self.db.execute(
            select(LabelingProject).where(
                LabelingProject.id == mapping_id,
                LabelingProject.deleted_at.is_(None)
            )
        )
        mapping = result.scalar_one_or_none()
        
        if mapping:
            logger.debug(f"Found mapping: {mapping.id}")
            return await self._to_response(mapping, include_template=include_template)
        
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
        
        if result.rowcount and result.rowcount > 0:  # type: ignore
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
        
        success = result.rowcount and result.rowcount > 0  # type: ignore
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
        # Convert rows to responses (async comprehension)
        responses = []
        for row in rows:
            response = await self._to_response_from_row(row, include_template=False)
            responses.append(response)
        return responses
    
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
        include_deleted: bool = False,
        include_template: bool = False
    ) -> Tuple[List[DatasetMappingResponse], int]:
        """
        获取所有映射及总数（用于分页）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            include_deleted: 是否包含已删除的记录
            include_template: 是否包含完整的模板信息
        """
        logger.debug(f"List all mappings with count, skip: {skip}, limit: {limit}, include_template={include_template}")
        
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

        # 过滤掉由自动标注任务自动创建的隐藏工程（configuration.autoTaskId 存在）
        filtered_rows = []
        for row in rows:
            mapping: LabelingProject = row[0]
            cfg = getattr(mapping, "configuration", None) or {}
            if isinstance(cfg, dict) and cfg.get("autoTaskId"):
                continue
            filtered_rows.append(row)

        logger.debug(
            f"Found {len(filtered_rows)} visible mappings (filtered from {len(rows)}), total: {total}"
        )
        # Convert rows to responses (async comprehension)
        responses = []
        for row in filtered_rows:
            response = await self._to_response_from_row(row, include_template=include_template)
            responses.append(response)
        # total 仍然返回数据库总数，目前前端只关注当前页内容数量，故不调整 total
        return responses, total
    
    async def get_template_id_by_dataset_id(self, dataset_id: str) -> Optional[str]:
        """
        Get template ID for a dataset by finding its labeling project
        
        Args:
            dataset_id: Dataset UUID
            
        Returns:
            Template ID or None if no labeling project found or no template associated
        """
        logger.debug(f"Looking up template for dataset: {dataset_id}")
        
        result = await self.db.execute(
            select(LabelingProject.template_id)
            .where(
                LabelingProject.dataset_id == dataset_id,
                LabelingProject.deleted_at.is_(None)
            )
            .limit(1)
        )
        
        template_id = result.scalar_one_or_none()
        
        if template_id:
            logger.debug(f"Found template {template_id} for dataset {dataset_id}")
        else:
            logger.warning(f"No template found for dataset {dataset_id}")
        
        return template_id
    
    async def get_mappings_by_source_with_count(
        self,
        dataset_id: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        include_template: bool = False
    ) -> Tuple[List[DatasetMappingResponse], int]:
        """
        根据源数据集ID获取映射关系及总数（用于分页）
        
        Args:
            dataset_id: 数据集ID
            skip: 跳过记录数
            limit: 返回记录数
            include_deleted: 是否包含已删除的记录
            include_template: 是否包含完整的模板信息
        """
        logger.debug(f"Get mappings by source dataset id with count: {dataset_id}, include_template={include_template}")
        
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

        # 过滤掉由自动标注任务自动创建的隐藏工程（configuration.autoTaskId 存在）
        filtered_rows = []
        for row in rows:
            mapping: LabelingProject = row[0]
            cfg = getattr(mapping, "configuration", None) or {}
            if isinstance(cfg, dict) and cfg.get("autoTaskId"):
                continue
            filtered_rows.append(row)

        logger.debug(
            f"Found {len(filtered_rows)} mappings for dataset {dataset_id} (filtered from {len(rows)}), total: {total}"
        )
        # Convert rows to responses (async comprehension)
        responses = []
        for row in filtered_rows:
            response = await self._to_response_from_row(row, include_template=include_template)
            responses.append(response)
        return responses, total