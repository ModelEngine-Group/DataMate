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

    async def create_dataset(
        self,
        name: str,
        dataset_type: str,
        description: str = "",
        status: Optional[str] = None,
    ) -> DatasetResponse:
        """
        创建数据集（参考Java版本DatasetApplicationService.createDataset）

        Args:
            name: 数据集名称
            dataset_type: 数据集类型（TEXT/IMAGE/VIDEO/AUDIO/OTHER）
            description: 数据集描述
            status: 数据集状态

        Returns:
            创建的数据集响应
        """
        try:
            logger.info(f"Creating dataset: {name}, type: {dataset_type}")

            # 1. 检查数据集名称是否已存在
            result = await self.db.execute(
                select(Dataset).where(Dataset.name == name)
            )
            existing_dataset = result.scalar_one_or_none()
            if existing_dataset:
                error_msg = f"Dataset with name '{name}' already exists"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 2. 创建数据集对象
            dataset_id = str(uuid.uuid4())
            dataset_path = f"{os.path.join('/dataset', dataset_id)}"

            # 如果没有提供status，默认为DRAFT
            if status is None:
                status = "DRAFT"

            new_dataset = Dataset(
                id=dataset_id,
                name=name,
                description=description,
                dataset_type=dataset_type,
                path=dataset_path,
                size_bytes=0,
                file_count=0,
                status=status,
                dataset_metadata="{}",
                version=0,
                created_by="system",
            )

            self.db.add(new_dataset)
            await self.db.flush()
            await self.db.commit()

            logger.info(f"Successfully created dataset: {new_dataset.id}")

            return DatasetResponse(
                id=new_dataset.id,  # type: ignore
                name=new_dataset.name,  # type: ignore
                description=new_dataset.description or "",  # type: ignore
                datasetType=new_dataset.dataset_type,  # type: ignore
                status=new_dataset.status,  # type: ignore
                fileCount=new_dataset.file_count or 0,  # type: ignore
                totalSize=new_dataset.size_bytes or 0,  # type: ignore
                createdAt=new_dataset.created_at,  # type: ignore
                updatedAt=new_dataset.updated_at,  # type: ignore
                createdBy=new_dataset.created_by  # type: ignore
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create dataset: {e}")
            raise Exception(f"Failed to create dataset: {str(e)}")

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
        完整格式: {"id": "...", "from_name": "x", "to_name": "y", "type": "...", "values": {"type": [...]}}

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

            # 获取并归一化现有标签
            existing_tags: List[Dict[str, Any]] = file_record.tags or []  # type: ignore

            def _normalize_tag(raw_tag: Dict[str, Any]) -> Dict[str, Any]:
                normalized = dict(raw_tag)
                if "values" not in normalized and isinstance(normalized.get("value"), dict):
                    normalized["values"] = normalized.get("value")
                normalized.pop("value", None)

                control_type = normalized.get("type")
                if isinstance(control_type, str) and control_type.strip():
                    normalized["type"] = control_type.strip().lower()

                values_obj = normalized.get("values")
                if isinstance(values_obj, dict):
                    normalized_values: Dict[str, Any] = {}
                    for value_key, value_content in values_obj.items():
                        key_str = str(value_key).strip().lower() if value_key is not None else ""
                        if key_str:
                            normalized_values[key_str] = value_content

                    if normalized_values:
                        normalized["values"] = normalized_values
                        if not normalized.get("type") and len(normalized_values) == 1:
                            normalized["type"] = next(iter(normalized_values.keys()))

                return normalized

            def _extract_tag_type(tag: Dict[str, Any]) -> str:
                control_type = tag.get("type")
                if isinstance(control_type, str) and control_type:
                    return control_type.strip().lower()
                values_obj = tag.get("values")
                if isinstance(values_obj, dict) and len(values_obj) == 1:
                    only_key = next(iter(values_obj.keys()))
                    if isinstance(only_key, str):
                        return only_key.strip().lower()
                return ""

            def _extract_name_pair(tag: Dict[str, Any]) -> Optional[tuple[str, str]]:
                from_name = tag.get("from_name") or tag.get("fromName")
                to_name = tag.get("to_name") or tag.get("toName")
                if not from_name or not to_name:
                    return None
                return str(from_name).strip(), str(to_name).strip()

            def _extract_from_name(tag: Dict[str, Any]) -> Optional[str]:
                from_name = tag.get("from_name") or tag.get("fromName")
                if not from_name:
                    return None
                return str(from_name).strip()

            def _extract_semantic_key(tag: Dict[str, Any]) -> Optional[tuple[str, str, str]]:
                name_pair = _extract_name_pair(tag)
                if not name_pair:
                    return None
                return name_pair[0], name_pair[1], _extract_tag_type(tag)

            existing_tags = [_normalize_tag(tag) for tag in existing_tags if isinstance(tag, dict)]

            tag_id_map: Dict[str, int] = {}
            tag_key_map: Dict[tuple[str, str, str], int] = {}
            tag_name_pair_map: Dict[tuple[str, str], int] = {}
            tag_from_name_map: Dict[str, int] = {}

            def _index_tag(idx: int, tag: Dict[str, Any]) -> None:
                tag_id = tag.get("id")
                if isinstance(tag_id, str) and tag_id:
                    tag_id_map[tag_id] = idx

                semantic_key = _extract_semantic_key(tag)
                if semantic_key:
                    tag_key_map[semantic_key] = idx

                name_pair = _extract_name_pair(tag)
                if name_pair:
                    tag_name_pair_map[name_pair] = idx

                from_name = _extract_from_name(tag)
                if from_name:
                    tag_from_name_map[from_name] = idx

            for idx, tag in enumerate(existing_tags):
                _index_tag(idx, tag)

            # 更新或追加标签
            for new_tag in processed_tags:
                if not isinstance(new_tag, dict):
                    continue

                normalized_new_tag = _normalize_tag(new_tag)
                tag_id = normalized_new_tag.get("id")

                if isinstance(tag_id, str) and tag_id in tag_id_map:
                    # 更新现有标签
                    idx = tag_id_map[tag_id]
                    existing_tags[idx] = normalized_new_tag
                    _index_tag(idx, normalized_new_tag)
                    logger.debug(f"Updated existing tag with id: {tag_id}")
                else:
                    semantic_key = _extract_semantic_key(normalized_new_tag)
                    name_pair = _extract_name_pair(normalized_new_tag)

                    matched_idx: Optional[int] = None

                    if semantic_key and semantic_key in tag_key_map:
                        matched_idx = tag_key_map[semantic_key]
                    elif name_pair and name_pair in tag_name_pair_map:
                        matched_idx = tag_name_pair_map[name_pair]
                    else:
                        from_name = _extract_from_name(normalized_new_tag)
                        if from_name and from_name in tag_from_name_map:
                            matched_idx = tag_from_name_map[from_name]

                    if matched_idx is not None:
                        existing_tag = existing_tags[matched_idx]
                        existing_id = existing_tag.get("id")
                        if not normalized_new_tag.get("id") and isinstance(existing_id, str) and existing_id:
                            normalized_new_tag["id"] = existing_id

                        if not normalized_new_tag.get("to_name") and isinstance(existing_tag.get("to_name"), str):
                            normalized_new_tag["to_name"] = existing_tag.get("to_name")
                        if not normalized_new_tag.get("from_name") and isinstance(existing_tag.get("from_name"), str):
                            normalized_new_tag["from_name"] = existing_tag.get("from_name")
                        if not normalized_new_tag.get("type") and isinstance(existing_tag.get("type"), str):
                            normalized_new_tag["type"] = str(existing_tag.get("type")).strip().lower()

                        existing_tags[matched_idx] = normalized_new_tag
                        _index_tag(matched_idx, normalized_new_tag)
                        logger.debug(
                            "Updated existing tag with semantic key: from_name=%s, to_name=%s, type=%s",
                            semantic_key[0] if semantic_key else (name_pair[0] if name_pair else ""),
                            semantic_key[1] if semantic_key else (name_pair[1] if name_pair else ""),
                            semantic_key[2] if semantic_key else ""
                        )
                    else:
                        # 追加新标签
                        existing_tags.append(normalized_new_tag)
                        appended_idx = len(existing_tags) - 1
                        _index_tag(appended_idx, normalized_new_tag)
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

                    # 创建硬链接（如果跨设备则回退到符号链接）
                    logger.info(f"creating hard link from {source_path} to {target_path}")
                    dst_dir = os.path.dirname(target_path)
                    await asyncio.to_thread(os.makedirs, dst_dir, exist_ok=True)
                    try:
                        # Try to create hard link first
                        await asyncio.to_thread(os.link, source_path, target_path)
                        logger.info(f"hard link created successfully")
                    except OSError as e:
                        # Hard link may fail due to cross-device link error, fall back to symbolic link
                        logger.warning(f"failed to create hard link from {source_path} to {target_path}: {e}, falling back to symbolic link")
                        await asyncio.to_thread(os.symlink, source_path, target_path)
                        logger.info(f"symbolic link created successfully")

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
        # Create hard link (fallback to symbolic link if cross-device)
        logger.info(f"creating hard link from {source_path} to {target_path}")
        dst_dir = os.path.dirname(target_path)
        await asyncio.to_thread(os.makedirs, dst_dir, exist_ok=True)
        try:
            # Try to create hard link first
            await asyncio.to_thread(os.link, source_path, target_path)
            logger.info(f"hard link created successfully")
        except OSError as e:
            # Hard link may fail due to cross-device link error, fall back to symbolic link
            logger.warning(f"failed to create hard link from {source_path} to {target_path}: {e}, falling back to symbolic link")
            await asyncio.to_thread(os.symlink, source_path, target_path)
            logger.info(f"symbolic link created successfully")
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
