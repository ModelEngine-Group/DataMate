import math
import os
import shutil
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Coroutine

from sqlalchemy import func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

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
                    tags_updated_at=f.tags_updated_at,  # type: ignore
                    annotation=getattr(f, "annotation", None),  # type: ignore
                )
                for f in files
            ]

            total_pages = math.ceil(total / size) if total > 0 else 0

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

    @staticmethod
    async def _get_or_create_dataset_directory(dataset: Dataset) -> str:
        """Get or create dataset directory"""
        dataset_dir = dataset.path
        os.makedirs(dataset_dir, exist_ok=True)
        return dataset_dir

    async def add_files_to_dataset(self, dataset_id: str, source_paths: List[str]):
        """
        Copy files to dataset directory and create corresponding database records

        Args:
            dataset_id: ID of the dataset
            source_paths: List of source file paths to copy

        Returns:
            List of created dataset file records
        """
        logger.info(f"Starting to add files to dataset {dataset_id}")

        try:
            # Get dataset and existing files
            dataset = await self.db.get(Dataset, dataset_id)
            if not dataset:
                logger.error(f"Dataset not found: {dataset_id}")
                return

            # Get existing files to check for duplicates
            result = await self.db.execute(
                select(DatasetFiles).where(DatasetFiles.dataset_id == dataset_id)
            )
            existing_files_map = dict()
            for dataset_file in result.scalars().all():
                existing_files_map.__setitem__(dataset_file.file_path, dataset_file)

            # Get or create dataset directory
            dataset_dir = await self._get_or_create_dataset_directory(dataset)

            # Process each source file
            for source_path in source_paths:
                try:
                    file_record = await self.create_new_dataset_file(dataset_dir, dataset_id, source_path)
                    if not file_record:
                        continue
                    await self.handle_dataset_file(dataset, existing_files_map, file_record, source_path)

                except Exception as e:
                    logger.error(f"Error processing file {source_path}: {str(e)}", e)
                    await self.db.rollback()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add files to dataset {dataset_id}: {str(e)}", exc_info=True)

    async def add_files_to_dataset_subdir(self, dataset_id: str, source_paths: List[str], subdir: str):
        """将文件添加到数据集下的指定子目录中，并创建对应的数据库记录。

        与 add_files_to_dataset 行为类似，但允许将文件放入形如
        ``<dataset.path>/<subdir>/<filename>`` 的结构中，适用于诸如
        "标注数据" 这类逻辑分组目录。
        """

        logger.info(f"Starting to add files to dataset {dataset_id} under subdir '{subdir}'")

        try:
            # Get dataset and existing files
            dataset = await self.db.get(Dataset, dataset_id)
            if not dataset:
                logger.error(f"Dataset not found: {dataset_id}")
                return

            # Get existing files to check for duplicates (按 file_path 去重)
            result = await self.db.execute(
                select(DatasetFiles).where(DatasetFiles.dataset_id == dataset_id)
            )
            existing_files_map: Dict[str, DatasetFiles] = {}
            for dataset_file in result.scalars().all():
                existing_files_map[dataset_file.file_path] = dataset_file  # type: ignore[attr-defined]

            # Get or create dataset root directory, then拼接子目录
            dataset_root = await self._get_or_create_dataset_directory(dataset)
            dataset_dir = os.path.join(dataset_root, subdir)
            os.makedirs(dataset_dir, exist_ok=True)

            # Process each source file
            for source_path in source_paths:
                try:
                    file_record = await self.create_new_dataset_file(dataset_dir, dataset_id, source_path)
                    if not file_record:
                        continue

                    target_path = file_record.file_path  # type: ignore[attr-defined]
                    file_size = file_record.file_size  # type: ignore[attr-defined]

                    # 如果同一 dataset_id + file_path 已存在，则更新大小，否则追加
                    if target_path in existing_files_map:
                        logger.warning(
                            f"File {target_path} already exists in dataset {dataset.id}, updating size only",
                        )
                        dataset_file = existing_files_map.get(target_path)
                        if dataset_file is not None:
                            dataset.size_bytes = (dataset.size_bytes or 0) - (dataset_file.file_size or 0) + file_size  # type: ignore[attr-defined]
                            dataset.updated_at = datetime.now()
                            dataset_file.file_size = file_size  # type: ignore[attr-defined]
                            dataset_file.updated_at = datetime.now()  # type: ignore[attr-defined]
                    else:
                        # 新文件：插入记录并更新统计
                        self.db.add(file_record)
                        dataset.file_count = (dataset.file_count or 0) + 1  # type: ignore[attr-defined]
                        dataset.size_bytes = (dataset.size_bytes or 0) + file_record.file_size  # type: ignore[attr-defined]
                        dataset.updated_at = datetime.now()
                        dataset.status = 'ACTIVE'

                    # 复制物理文件到目标路径
                    logger.info(f"copy file {source_path} to {target_path}")
                    dst_dir = os.path.dirname(target_path)
                    await asyncio.to_thread(os.makedirs, dst_dir, exist_ok=True)
                    await asyncio.to_thread(shutil.copy2, source_path, target_path)

                    await self.db.commit()

                except Exception as e:
                    logger.error(f"Error processing file {source_path} into subdir {subdir}: {str(e)}", e)
                    await self.db.rollback()

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to add files to dataset {dataset_id} under subdir '{subdir}': {str(e)}",
                exc_info=True,
            )

    async def handle_dataset_file(self, dataset, existing_files_map: dict[Any, Any], file_record: DatasetFiles, source_path: str):
        target_path = file_record.file_path
        file_size = file_record.file_size
        file_name = file_record.file_name

        # Check for duplicate by filename
        if target_path in existing_files_map:
            logger.warning(f"File with name {file_name} already exists in dataset {dataset.id}")
            dataset_file = existing_files_map.get(target_path)
            dataset.size_bytes = dataset.size_bytes - dataset_file.file_size + file_size
            dataset.updated_at = datetime.now()
            dataset_file.file_size = file_size
            dataset_file.updated_at = datetime.now()
        else:
            # Add to database
            self.db.add(file_record)
            dataset.file_count = dataset.file_count + 1
            dataset.size_bytes = dataset.size_bytes + file_record.file_size
            dataset.updated_at = datetime.now()
            dataset.status = 'ACTIVE'
        # Copy file
        logger.info(f"copy file {source_path} to {target_path}")
        dst_dir = os.path.dirname(target_path)
        await asyncio.to_thread(os.makedirs, dst_dir, exist_ok=True)
        await asyncio.to_thread(shutil.copy2, source_path, target_path)
        await self.db.commit()

    @staticmethod
    async def create_new_dataset_file(dataset_dir: str, dataset_id: str, source_path: str) -> DatasetFiles | None:
        source_path_obj = Path(source_path)

        # Check if source exists and is a file
        if not source_path_obj.exists() or not source_path_obj.is_file():
            logger.warning(f"Source file does not exist or is not a file: {source_path}")
            return None
        file_name = source_path_obj.name
        file_extension = os.path.splitext(file_name)[1].lstrip('.').lower()
        file_size = source_path_obj.stat().st_size
        target_path = os.path.join(dataset_dir, file_name)
        file_record = DatasetFiles(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            file_name=file_name,
            file_type=file_extension or 'other',
            file_size=file_size,
            file_path=target_path,
            upload_time=datetime.now(),
            last_access_time=datetime.now(),
            status='ACTIVE',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return file_record
