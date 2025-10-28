from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.dm_service import DatasetResponse, PagedDatasetFileResponse, DatasetFileResponse
from app.models.dm.dataset import Dataset
from app.models.dm.dataset_files import DatasetFiles

logger = get_logger(__name__)

class Client:
    """数据管理服务客户端 - 直接访问数据库"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化 DM 客户端
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.info("Initialize DM service client (Database mode)")

    async def get_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """获取数据集详情"""
        try:
            logger.info(f"Getting dataset detail: {dataset_id} ...")
            
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
            logger.info(f"Get dataset files: dataset={dataset_id}, page={page}, size={size}")
            
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
                    lastAccessTime=f.last_access_time  # type: ignore
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