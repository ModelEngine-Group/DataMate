from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Dataset, DatasetFiles

from ..schema import DatasetResponse, PagedDatasetFileResponse, DatasetFileResponse

logger = get_logger(__name__)

class Service:
    """数据管理服务客户端 - 直接访问数据库"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化 DM 客户端
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("Initialize DM service client (Database mode)")

    async def get_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """获取数据集详情"""
        try:
            logger.debug(f"Getting dataset detail: {dataset_id} ...")
            
            result = await self.db.execute(
                select(Dataset).where(Dataset.id == dataset_id)
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                logger.error(f"Dataset not found: {dataset_id}")
                return None
            
            # 将数据库模型转换为响应模型
            # type: ignore 用于忽略 SQLAlchemy 的类型检查问题
            return DatasetResponse(
                id=dataset.id,  # type: ignore
                name=dataset.name,  # type: ignore
                description=dataset.description or "",  # type: ignore
                datasetType=dataset.dataset_type,  # type: ignore
                status=dataset.status,  # type: ignore
                fileCount=dataset.file_count or 0,  # type: ignore
                totalSize=dataset.size_bytes or 0,  # type: ignore
                createdAt=dataset.created_at,  # type: ignore
                updatedAt=dataset.updated_at,  # type: ignore
                createdBy=dataset.created_by  # type: ignore
            )
        except Exception as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            return None
    
    async def get_dataset_files(
        self, 
        dataset_id: str, 
        page: int = 0, 
        size: int = 100,
        file_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[PagedDatasetFileResponse]:
        """获取数据集文件列表"""
        try:
            logger.debug(f"Get dataset files: dataset={dataset_id}, page={page}, size={size}")
            
            # 构建查询
            query = select(DatasetFiles).where(DatasetFiles.dataset_id == dataset_id)
            
            # 添加可选过滤条件
            if file_type:
                query = query.where(DatasetFiles.file_type == file_type)
            if status:
                query = query.where(DatasetFiles.status == status)
            
            # 获取总数
            count_query = select(func.count()).select_from(DatasetFiles).where(
                DatasetFiles.dataset_id == dataset_id
            )
            if file_type:
                count_query = count_query.where(DatasetFiles.file_type == file_type)
            if status:
                count_query = count_query.where(DatasetFiles.status == status)
                
            count_result = await self.db.execute(count_query)
            total = count_result.scalar_one()
            
            # 分页查询
            query = query.offset(page * size).limit(size).order_by(DatasetFiles.created_at.desc())
            result = await self.db.execute(query)
            files = result.scalars().all()
            
            # 转换为响应模型
            # type: ignore 用于忽略 SQLAlchemy 的类型检查问题
            content = [
                DatasetFileResponse(
                    id=f.id,  # type: ignore
                    fileName=f.file_name,  # type: ignore
                    fileType=f.file_type or "",  # type: ignore
                    filePath=f.file_path,  # type: ignore
                    originalName=f.file_name,  # type: ignore
                    size=f.file_size,  # type: ignore
                    status=f.status,  # type: ignore
                    uploadedAt=f.upload_time,  # type: ignore
                    description=None,
                    uploadedBy=None,
                    lastAccessTime=f.last_access_time,  # type: ignore
                    tags=f.tags,  # type: ignore
                    tags_updated_at=f.tags_updated_at  # type: ignore
                )
                for f in files
            ]
            
            total_pages = (total + size - 1) // size if size > 0 else 0
            
            return PagedDatasetFileResponse(
                content=content,
                totalElements=total,
                totalPages=total_pages,
                page=page,
                size=size
            )
        except Exception as e:
            logger.error(f"Failed to get dataset files for {dataset_id}: {e}")
            return None
    
    async def download_file(self, dataset_id: str, file_id: str) -> Optional[bytes]:
        """
        下载文件内容
        注意：此方法保留接口兼容性，但实际文件下载可能需要通过文件系统或对象存储
        """
        logger.warning(f"download_file is deprecated when using database mode. Use get_file_download_url instead.")
        return None
    
    async def get_file_download_url(self, dataset_id: str, file_id: str) -> Optional[str]:
        """获取文件下载URL（或文件路径）"""
        try:
            result = await self.db.execute(
                select(DatasetFiles).where(
                    DatasetFiles.id == file_id,
                    DatasetFiles.dataset_id == dataset_id
                )
            )
            file = result.scalar_one_or_none()
            
            if not file:
                logger.error(f"File not found: {file_id} in dataset {dataset_id}")
                return None
            
            # 返回文件路径（可以是本地路径或对象存储URL）
            return file.file_path  # type: ignore
        except Exception as e:
            logger.error(f"Failed to get file path for {file_id}: {e}")
            return None
    
    async def close(self):
        """关闭客户端连接（数据库模式下无需操作）"""
        logger.info("DM service client closed (Database mode)")
    
    async def update_file_tags_partial(
        self, 
        file_id: str, 
        new_tags: List[Dict[str, Any]],
        template_id: Optional[str] = None
    ) -> tuple[bool, Optional[str], Optional[datetime]]:
        """
        部分更新文件标签，支持自动格式转换
        
        如果提供了 template_id，会自动将简化格式的标签转换为完整格式。
        简化格式: {"from_name": "x", "to_name": "y", "values": [...]}
        完整格式: {"id": "...", "from_name": "x", "to_name": "y", "type": "...", "value": {"type": [...]}}
        
        Args:
            file_id: 文件ID
            new_tags: 新的标签列表（部分更新），可以是简化格式或完整格式
            template_id: 可选的模板ID，用于格式转换
        
        Returns:
            (成功标志, 错误信息, 更新时间)
        """
        try:
            logger.info(f"Partial updating tags for file: {file_id}")
            
            # 获取文件记录
            result = await self.db.execute(
                select(DatasetFiles).where(DatasetFiles.id == file_id)
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                logger.error(f"File not found: {file_id}")
                return False, f"File not found: {file_id}", None
            
            # 如果提供了 template_id，尝试进行格式转换
            processed_tags = new_tags
            if template_id:
                logger.debug(f"Converting tags using template: {template_id}")
                
                try:
                    # 获取模板配置
                    from app.db.models import AnnotationTemplate
                    template_result = await self.db.execute(
                        select(AnnotationTemplate).where(
                            AnnotationTemplate.id == template_id,
                            AnnotationTemplate.deleted_at.is_(None)
                        )
                    )
                    template = template_result.scalar_one_or_none()
                    
                    if not template:
                        logger.warning(f"Template {template_id} not found, skipping conversion")
                    else:
                        # 使用 converter 转换标签格式
                        from app.module.annotation.utils import create_converter_from_template_config
                        
                        converter = create_converter_from_template_config(template.configuration)  # type: ignore
                        processed_tags = converter.convert_if_needed(new_tags)
                        
                        logger.info(f"Converted {len(new_tags)} tags to full format")
                        
                except Exception as e:
                    logger.error(f"Failed to convert tags using template: {e}")
                    # 继续使用原始标签格式
                    logger.warning("Continuing with original tag format")
            
            # 获取现有标签
            existing_tags: List[Dict[str, Any]] = file_record.tags or []  # type: ignore
            
            # 创建标签ID到索引的映射
            tag_id_map = {tag.get('id'): idx for idx, tag in enumerate(existing_tags) if tag.get('id')}
            
            # 更新或追加标签
            for new_tag in processed_tags:
                tag_id = new_tag.get('id')
                if tag_id and tag_id in tag_id_map:
                    # 更新现有标签
                    idx = tag_id_map[tag_id]
                    existing_tags[idx] = new_tag
                    logger.debug(f"Updated existing tag with id: {tag_id}")
                else:
                    # 追加新标签
                    existing_tags.append(new_tag)
                    logger.debug(f"Added new tag with id: {tag_id}")
            
            # 更新数据库
            update_time = datetime.utcnow()
            file_record.tags = existing_tags  # type: ignore
            file_record.tags_updated_at = update_time  # type: ignore
            
            await self.db.commit()
            await self.db.refresh(file_record)
            
            logger.info(f"Successfully updated tags for file: {file_id}")
            return True, None, update_time
            
        except Exception as e:
            logger.error(f"Failed to update tags for file {file_id}: {e}")
            await self.db.rollback()
            return False, str(e), None