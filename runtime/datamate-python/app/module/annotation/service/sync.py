from typing import Optional, List, Dict, Any, Tuple, Set
from app.module.dataset import DatasetManagementService
from sqlalchemy import update, select
from app.db.models import DatasetFiles

from app.core.logging import get_logger
from app.core.config import settings
from app.exception import NoDatasetInfoFoundError

from ..client import LabelStudioClient
from ..schema import (
    SyncDatasetResponse,
    DatasetMappingResponse,
    SyncAnnotationsResponse
)
from ..service.mapping import DatasetMappingService

logger = get_logger(__name__)

class SyncService:
    """数据同步服务"""
    
    def __init__(
        self, 
        dm_client: DatasetManagementService, 
        ls_client: LabelStudioClient,
        mapping_service: DatasetMappingService
    ):
        self.dm_client = dm_client
        self.ls_client = ls_client
        self.mapping_service = mapping_service
    
    def _determine_data_type(self, file_type: str) -> str:
        """根据文件类型确定数据类型"""
        file_type_lower = file_type.lower()
        
        type_mapping = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg'],
            'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'],
            'text': ['txt', 'doc', 'docx', 'pdf'],
            'wsi': ['svs', 'tiff', 'ndpi', 'mrxs', 'sdpc'],
            'ct': ['dcm', 'dicom', 'nii', 'nii.gz']
        }
        
        for data_type, extensions in type_mapping.items():
            if any(ext in file_type_lower for ext in extensions):
                return data_type
        
        return 'image'  # 默认为图像类型
    
    def _build_task_data(self, file_info: Any, dataset_id: str) -> dict:
        """构建Label Studio任务数据"""
        data_type = self._determine_data_type(file_info.fileType)
        
        # 替换文件路径前缀
        file_path = file_info.filePath.removeprefix(settings.dm_file_path_prefix)
        file_path = settings.label_studio_file_path_prefix + file_path
        
        return {
            "data": {
                f"{data_type}": file_path,
                "file_path": file_info.filePath,
                "file_id": file_info.id,
                "original_name": file_info.originalName,
                "dataset_id": dataset_id,
            }
        }
    
    async def _create_tasks_with_fallback(
        self, 
        project_id: str, 
        tasks: List[dict]
    ) -> int:
        """批量创建任务，失败时回退到单个创建"""
        if not tasks:
            return 0
        
        # 尝试批量创建
        batch_result = await self.ls_client.create_tasks_batch(project_id, tasks)
        
        if batch_result:
            logger.debug(f"Successfully created {len(tasks)} tasks in batch")
            return len(tasks)
        
        # 批量失败，回退到单个创建
        logger.warning(f"Batch creation failed, falling back to single creation")
        created_count = 0
        
        for task_data in tasks:
            task_result = await self.ls_client.create_task(
                project_id,
                task_data["data"],
                task_data.get("meta")
            )
            if task_result:
                created_count += 1
        
        logger.debug(f"Successfully created {created_count}/{len(tasks)} tasks individually")
        return created_count
    
    async def get_existing_dm_file_mapping(self, project_id: str) -> Dict[str, int]:
        """
        获取Label Studio项目中已存在的DM文件ID到任务ID的映射
        
        Args:
            project_id: Label Studio项目ID
            
        Returns:
            file_id到task_id的映射字典
        """
        try:
            page_size = getattr(settings, 'ls_task_page_size', 1000)
            result = await self.ls_client.get_project_tasks(
                project_id=project_id,
                page=None,
                page_size=page_size
            )

            if not result:
                logger.warning(f"Failed to fetch tasks for project {project_id}")
                return {}
            
            all_tasks = result.get("tasks", [])
            logger.info(f"Successfully fetched {len(all_tasks)} tasks")

            # 使用字典推导式构建映射
            dm_file_to_task_mapping = {
                str(task.get('data', {}).get('file_id')): task.get('id')
                for task in all_tasks
                if task.get('data', {}).get('file_id') is not None
            }
            
            logger.info(f"Found {len(dm_file_to_task_mapping)} existing task mappings")
            return dm_file_to_task_mapping

        except Exception as e:
            logger.error(f"Error while fetching existing tasks: {e}")
            return {}
    
    async def _fetch_dm_files_paginated(
        self, 
        dataset_id: str, 
        batch_size: int,
        existing_file_ids: Set[str],
        project_id: str
    ) -> Tuple[Set[str], int]:
        """
        分页获取DM文件并创建新任务
        
        Returns:
            (当前文件ID集合, 创建的任务数)
        """
        current_file_ids = set()
        total_created = 0
        page = 0
        
        while True:
            files_response = await self.dm_client.get_dataset_files(
                dataset_id, 
                page=page, 
                size=batch_size,
            )
            
            if not files_response or not files_response.content:
                logger.info(f"No more files on page {page + 1}")
                break
            
            logger.info(f"Processing page {page + 1}, {len(files_response.content)} files")
            
            # 筛选新文件并构建任务数据
            new_tasks = []
            for file_info in files_response.content:
                file_id = str(file_info.id)
                current_file_ids.add(file_id)
                
                if file_id not in existing_file_ids:
                    task_data = self._build_task_data(file_info, dataset_id)
                    new_tasks.append(task_data)
            
            logger.info(f"Page {page + 1}: {len(new_tasks)} new files, {len(files_response.content) - len(new_tasks)} existing")
            
            # 批量创建任务
            if new_tasks:
                created = await self._create_tasks_with_fallback(project_id, new_tasks)
                total_created += created
            
            # 检查是否还有更多页面
            if page >= files_response.totalPages - 1:
                break
            page += 1
        
        return current_file_ids, total_created
    
    async def _delete_orphaned_tasks(
        self,
        existing_dm_file_mapping: Dict[str, int],
        current_file_ids: Set[str]
    ) -> int:
        """删除在DM中不存在的Label Studio任务"""
        # 使用集合操作找出需要删除的文件ID
        deleted_file_ids = set(existing_dm_file_mapping.keys()) - current_file_ids
        
        if not deleted_file_ids:
            logger.info("No tasks to delete")
            return 0
        
        tasks_to_delete = [existing_dm_file_mapping[fid] for fid in deleted_file_ids]
        logger.info(f"Deleting {len(tasks_to_delete)} orphaned tasks")
        
        delete_result = await self.ls_client.delete_tasks_batch(tasks_to_delete)
        deleted_count = delete_result.get("successful", 0)
        
        logger.info(f"Successfully deleted {deleted_count} tasks")
        return deleted_count
    
    async def sync_dataset_files(
        self, 
        mapping_id: str, 
        batch_size: int = 50
    ) -> SyncDatasetResponse:
        """
        同步数据集文件到Label Studio (Legacy endpoint - 委托给sync_files)
        
        Args:
            mapping_id: 映射ID
            batch_size: 批处理大小
            
        Returns:
            同步结果响应
        """
        logger.info(f"Start syncing dataset files by mapping: {mapping_id}")
        
        # 获取映射关系
        mapping = await self.mapping_service.get_mapping_by_uuid(mapping_id)
        if not mapping:
            logger.error(f"Dataset mapping not found: {mapping_id}")
            return SyncDatasetResponse(
                id="",
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Dataset mapping not found: {mapping_id}"
            )
        
        try:
            # 委托给sync_files执行实际同步
            result = await self.sync_files(mapping, batch_size)
            
            logger.info(f"Sync completed: created={result['created']}, deleted={result['deleted']}, total={result['total']}")
            
            return SyncDatasetResponse(
                id=mapping.id,
                status="success",
                synced_files=result["created"],
                total_files=result["total"],
                message=f"Sync completed: created {result['created']} files, deleted {result['deleted']} tasks"
            )
            
        except Exception as e:
            logger.error(f"Error while syncing dataset: {e}")
            return SyncDatasetResponse(
                id=mapping.id,
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Sync failed: {str(e)}"
            )
        
    async def sync_dataset(
        self, 
        mapping_id: str, 
        batch_size: int = 50, 
        file_priority: int = 0, 
        annotation_priority: int = 0
    ) -> SyncDatasetResponse:
        """
        同步数据集文件和标注
        
        Args:
            mapping_id: 映射ID
            batch_size: 批处理大小
            file_priority: 文件同步优先级 (0: dataset优先, 1: annotation优先)
            annotation_priority: 标注同步优先级 (0: dataset优先, 1: annotation优先)
            
        Returns:
            同步结果响应
        """
        logger.info(f"Start syncing dataset by mapping: {mapping_id}")
        
        # 检查映射是否存在
        mapping = await self.mapping_service.get_mapping_by_uuid(mapping_id)
        if not mapping:
            logger.error(f"Dataset mapping not found: {mapping_id}")
            return SyncDatasetResponse(
                id="",
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Dataset mapping not found: {mapping_id}"
            )
        
        try:
            # 同步文件
            file_result = await self.sync_files(mapping, batch_size)
            
            # TODO: 同步标注
            # annotation_result = await self.sync_annotations(mapping, batch_size, annotation_priority)
            
            logger.info(f"Sync completed: created={file_result['created']}, deleted={file_result['deleted']}, total={file_result['total']}")
            
            return SyncDatasetResponse(
                id=mapping.id,
                status="success",
                synced_files=file_result["created"],
                total_files=file_result["total"],
                message=f"Sync completed: created {file_result['created']} files, deleted {file_result['deleted']} tasks"
            )
            
        except Exception as e:
            logger.error(f"Error while syncing dataset: {e}")
            return SyncDatasetResponse(
                id=mapping.id,
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Sync failed: {str(e)}"
            )
        
    async def sync_files(
        self, 
        mapping: DatasetMappingResponse, 
        batch_size: int
    ) -> Dict[str, int]:
        """
        同步DM和Label Studio之间的文件
        
        Args:
            mapping: 数据集映射信息
            batch_size: 批处理大小
            
        Returns:
            同步统计信息: {"created": int, "deleted": int, "total": int}
        """
        logger.info(f"Syncing files for dataset {mapping.dataset_id} to project {mapping.labeling_project_id}")
        
        # 获取DM数据集信息
        dataset_info = await self.dm_client.get_dataset(mapping.dataset_id)
        if not dataset_info:
            raise NoDatasetInfoFoundError(mapping.dataset_id)
        
        total_files = dataset_info.fileCount
        logger.info(f"Total files in DM dataset: {total_files}")

        # 获取Label Studio中已存在的文件映射
        existing_dm_file_mapping = await self.get_existing_dm_file_mapping(mapping.labeling_project_id)
        existing_file_ids = set(existing_dm_file_mapping.keys())
        logger.info(f"{len(existing_file_ids)} tasks already exist in Label Studio")
        
        # 分页获取DM文件并创建新任务
        current_file_ids, created_count = await self._fetch_dm_files_paginated(
            mapping.dataset_id,
            batch_size,
            existing_file_ids,
            mapping.labeling_project_id
        )
        
        # 删除孤立任务
        deleted_count = await self._delete_orphaned_tasks(
            existing_dm_file_mapping,
            current_file_ids
        )
        
        logger.info(f"File sync completed: total={total_files}, created={created_count}, deleted={deleted_count}")
        
        return {
            "created": created_count,
            "deleted": deleted_count,
            "total": total_files
        }

    async def sync_annotations(
        self, 
        mapping: DatasetMappingResponse, 
        batch_size: int, 
        priority: int
    ) -> Dict[str, int]:
        """
        同步DM和Label Studio之间的标注
        
        Args:
            mapping: 数据集映射信息
            batch_size: 批处理大小
            priority: 标注同步优先级 (0: dataset优先, 1: annotation优先)
            
        Returns:
            同步统计信息: {"synced_to_dm": int, "synced_to_ls": int}
        """
        logger.info(f"Syncing annotations for dataset {mapping.dataset_id} (priority={priority})")
        
        # TODO: 实现标注同步逻辑
        # 1. 从DM获取标注结果
        # 2. 从Label Studio获取标注结果
        # 3. 根据优先级合并结果
        # 4. 将差异写入DM和LS
        
        logger.info("Annotation sync not yet implemented")
        return {
            "synced_to_dm": 0,
            "synced_to_ls": 0
        }
    
    def _simplify_annotation_result(self, annotation: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
        """
        将Label Studio标注结果简化为指定格式
        
        Args:
            annotation: Label Studio原始标注数据
            
        Returns:
            Tuple of (简化后的标注结果列表, 标注更新时间ISO字符串)
        """
        simplified = []
        
        # 获取result字段（包含实际的标注数据）
        results = annotation.get("result", [])
        
        # 获取标注的更新时间，优先使用updated_at，否则使用created_at
        updated_at = annotation.get("updated_at") or annotation.get("created_at", "")
        
        for result_item in results:
            simplified_item = {
                "from_name": result_item.get("from_name", ""),
                "to_name": result_item.get("to_name", ""),
                "type": result_item.get("type", ""),
                "values": result_item.get("value", {})
            }
            simplified.append(simplified_item)
        
        return simplified, updated_at
    
    def _compare_timestamps(self, ts1: str, ts2: str) -> int:
        """
        比较两个ISO格式时间戳
        
        Args:
            ts1: 第一个时间戳
            ts2: 第二个时间戳
            
        Returns:
            1 如果 ts1 > ts2
            -1 如果 ts1 < ts2
            0 如果相等或无法比较
        """
        try:
            from dateutil import parser
            from datetime import timezone
            
            dt1 = parser.parse(ts1)
            dt2 = parser.parse(ts2)
            
            # Convert both to UTC timezone-aware if needed
            if dt1.tzinfo is None:
                dt1 = dt1.replace(tzinfo=timezone.utc)
            if dt2.tzinfo is None:
                dt2 = dt2.replace(tzinfo=timezone.utc)
            
            if dt1 > dt2:
                return 1
            elif dt1 < dt2:
                return -1
            else:
                return 0
        except Exception as e:
            logger.warning(f"Failed to compare timestamps {ts1} and {ts2}: {e}")
            return 0
    
    def _should_overwrite_dm(self, ls_updated_at: str, dm_tags_updated_at: Optional[str], overwrite: bool) -> bool:
        """
        判断是否应该用Label Studio的标注覆盖DataMate的标注
        
        Args:
            ls_updated_at: Label Studio标注的更新时间
            dm_tags_updated_at: DataMate中标注的更新时间（从tags_updated_at字段）
            overwrite: 是否允许覆盖
            
        Returns:
            True 如果应该覆盖，False 如果不应该覆盖
        """
        # 如果不允许覆盖，直接返回False
        if not overwrite:
            return False
        
        # 如果DataMate没有标注时间戳，允许覆盖
        if not dm_tags_updated_at:
            return True
        
        # 如果Label Studio的标注更新，允许覆盖
        return self._compare_timestamps(ls_updated_at, dm_tags_updated_at) > 0
    
    def _should_overwrite_ls(self, dm_tags_updated_at: Optional[str], ls_updated_at: str, overwrite_ls: bool) -> bool:
        """
        判断是否应该用DataMate的标注覆盖Label Studio的标注
        
        Args:
            dm_tags_updated_at: DataMate中标注的更新时间（从tags_updated_at字段）
            ls_updated_at: Label Studio标注的更新时间
            overwrite_ls: 是否允许覆盖Label Studio
            
        Returns:
            True 如果应该覆盖，False 如果不应该覆盖
        """
        # 如果不允许覆盖，直接返回False
        if not overwrite_ls:
            return False
        
        # 如果DataMate没有标注时间戳，不应该覆盖Label Studio
        if not dm_tags_updated_at:
            return False
        
        # 如果Label Studio没有标注，应该覆盖
        if not ls_updated_at:
            return True
        
        # 如果DataMate的标注更新，允许覆盖
        return self._compare_timestamps(dm_tags_updated_at, ls_updated_at) > 0
    
    async def sync_annotations_from_ls_to_dm(
        self,
        mapping: DatasetMappingResponse,
        batch_size: int = 50,
        overwrite: bool = True
    ) -> SyncAnnotationsResponse:
        """
        从Label Studio同步标注到数据集
        
        Args:
            mapping: 数据集映射信息
            batch_size: 批处理大小
            overwrite: 是否允许覆盖DataMate中的标注（基于时间戳比较）
            
        Returns:
            同步结果响应
        """
        logger.info(f"Syncing annotations from LS to DM: dataset={mapping.dataset_id}, project={mapping.labeling_project_id}")
        
        synced_count = 0
        skipped_count = 0
        failed_count = 0
        conflicts_resolved = 0
        
        try:
            # 获取Label Studio中的所有任务
            ls_tasks_result = await self.ls_client.get_project_tasks(
                mapping.labeling_project_id,
                page=None
            )
            
            if not ls_tasks_result:
                token_display = settings.label_studio_user_token[:10] + "..." if settings.label_studio_user_token else "None"
                error_msg = f"Failed to fetch tasks from Label Studio project {mapping.labeling_project_id}. Please check:\n" \
                           f"1. Label Studio is running at {settings.label_studio_base_url}\n" \
                           f"2. Project ID {mapping.labeling_project_id} exists\n" \
                           f"3. API token is valid: {token_display}"
                logger.error(error_msg)
                return SyncAnnotationsResponse(
                    id=mapping.id,
                    status="error",
                    synced_to_dm=0,
                    synced_to_ls=0,
                    skipped=0,
                    failed=0,
                    conflicts_resolved=0,
                    message=f"Failed to connect to Label Studio at {settings.label_studio_base_url}"
                )
            
            all_tasks = ls_tasks_result.get("tasks", [])
            logger.info(f"Found {len(all_tasks)} tasks in Label Studio project")
            
            if len(all_tasks) == 0:
                logger.warning(f"No tasks found in Label Studio project {mapping.labeling_project_id}")
                return SyncAnnotationsResponse(
                    id=mapping.id,
                    status="success",
                    synced_to_dm=0,
                    synced_to_ls=0,
                    skipped=0,
                    failed=0,
                    conflicts_resolved=0,
                    message="No tasks found in Label Studio project"
                )
            
            # 批量处理任务
            for i in range(0, len(all_tasks), batch_size):
                batch_tasks = all_tasks[i:i + batch_size]
                logger.info(f"Processing batch {i // batch_size + 1}, {len(batch_tasks)} tasks")
                
                for task in batch_tasks:
                    task_id = task.get("id")
                    file_id = task.get("data", {}).get("file_id")
                    
                    if not file_id:
                        logger.warning(f"Task {task_id} has no file_id, skipping")
                        skipped_count += 1
                        continue
                    
                    # 获取任务的标注结果
                    annotations = await self.ls_client.get_task_annotations(task_id)
                    
                    if not annotations:
                        logger.debug(f"No annotations for task {task_id}, skipping")
                        skipped_count += 1
                        continue
                    
                    # 简化标注结果（取最新的标注）
                    latest_annotation = max(annotations, key=lambda a: a.get("updated_at") or a.get("created_at", ""))
                    simplified_annotations, ls_updated_at = self._simplify_annotation_result(latest_annotation)
                    
                    if not simplified_annotations:
                        logger.debug(f"Task {task_id} has no valid annotation results")
                        skipped_count += 1
                        continue
                    
                    # 更新数据库中的tags字段
                    try:
                        # 检查文件是否存在以及是否已有标注
                        result = await self.dm_client.db.execute(
                            select(DatasetFiles).where(
                                DatasetFiles.id == file_id,
                                DatasetFiles.dataset_id == mapping.dataset_id
                            )
                        )
                        file_record = result.scalar_one_or_none()
                        
                        if not file_record:
                            logger.warning(f"File {file_id} not found in dataset {mapping.dataset_id}")
                            failed_count += 1
                            continue
                        
                        # 检查是否应该覆盖DataMate的标注（使用文件级别的tags_updated_at）
                        dm_tags_updated_at: Optional[str] = None
                        if file_record.tags_updated_at:  # type: ignore
                            dm_tags_updated_at = file_record.tags_updated_at.isoformat()  # type: ignore
                        
                        if not self._should_overwrite_dm(ls_updated_at, dm_tags_updated_at, overwrite):
                            logger.debug(f"File {file_id}: DataMate has newer or equal annotations, skipping (overwrite={overwrite})")
                            skipped_count += 1
                            continue
                        
                        # 如果存在冲突（两边都有标注且时间戳不同），记录为冲突解决
                        if file_record.tags and ls_updated_at:  # type: ignore
                            conflicts_resolved += 1
                            logger.debug(f"File {file_id}: Resolved conflict, Label Studio annotation is newer")
                        
                        # 更新tags字段和tags_updated_at
                        from datetime import datetime
                        tags_updated_datetime = datetime.fromisoformat(ls_updated_at.replace('Z', '+00:00'))
                        
                        await self.dm_client.db.execute(
                            update(DatasetFiles)
                            .where(DatasetFiles.id == file_id)
                            .values(
                                tags=simplified_annotations,
                                tags_updated_at=tags_updated_datetime
                            )
                        )
                        await self.dm_client.db.commit()
                        
                        synced_count += 1
                        logger.debug(f"Synced annotations for file {file_id}: {len(simplified_annotations)} results")
                        
                    except Exception as e:
                        logger.error(f"Failed to update annotations for file {file_id}: {e}")
                        failed_count += 1
                        await self.dm_client.db.rollback()
            
            logger.info(f"Annotation sync completed: synced={synced_count}, skipped={skipped_count}, failed={failed_count}, conflicts_resolved={conflicts_resolved}")
            
            status = "success" if failed_count == 0 else ("partial" if synced_count > 0 else "error")
            
            return SyncAnnotationsResponse(
                id=mapping.id,
                status=status,
                synced_to_dm=synced_count,
                synced_to_ls=0,
                skipped=skipped_count,
                failed=failed_count,
                conflicts_resolved=conflicts_resolved,
                message=f"Synced {synced_count} annotations from Label Studio to dataset. Skipped: {skipped_count}, Failed: {failed_count}, Conflicts resolved: {conflicts_resolved}"
            )
            
        except Exception as e:
            logger.error(f"Error while syncing annotations from LS to DM: {e}")
            return SyncAnnotationsResponse(
                id=mapping.id,
                status="error",
                synced_to_dm=synced_count,
                synced_to_ls=0,
                skipped=skipped_count,
                failed=failed_count,
                conflicts_resolved=conflicts_resolved,
                message=f"Sync failed: {str(e)}"
            )
    
    async def sync_annotations_from_dm_to_ls(
        self,
        mapping: DatasetMappingResponse,
        batch_size: int = 50,
        overwrite_ls: bool = True
    ) -> SyncAnnotationsResponse:
        """
        从DataMate数据集同步标注到Label Studio
        
        Args:
            mapping: 数据集映射信息
            batch_size: 批处理大小
            overwrite_ls: 是否允许覆盖Label Studio中的标注（基于时间戳比较）
            
        Returns:
            同步结果响应
        """
        logger.info(f"Syncing annotations from DM to LS: dataset={mapping.dataset_id}, project={mapping.labeling_project_id}")
        
        synced_count = 0
        skipped_count = 0
        failed_count = 0
        conflicts_resolved = 0
        
        try:
            # 获取Label Studio中的文件ID到任务ID的映射
            dm_file_to_task_mapping = await self.get_existing_dm_file_mapping(mapping.labeling_project_id)
            
            if not dm_file_to_task_mapping:
                logger.warning(f"No task mapping found for project {mapping.labeling_project_id}")
                return SyncAnnotationsResponse(
                    id=mapping.id,
                    status="error",
                    synced_to_dm=0,
                    synced_to_ls=0,
                    skipped=0,
                    failed=0,
                    conflicts_resolved=0,
                    message="No tasks found in Label Studio project"
                )
            
            logger.info(f"Found {len(dm_file_to_task_mapping)} task mappings")
            
            # 分页获取DataMate中的文件
            page = 0
            processed_count = 0
            
            while True:
                files_response = await self.dm_client.get_dataset_files(
                    mapping.dataset_id,
                    page=page,
                    size=batch_size,
                )
                
                if not files_response or not files_response.content:
                    logger.info(f"No more files on page {page + 1}")
                    break
                
                logger.info(f"Processing page {page + 1}, {len(files_response.content)} files")
                
                for file_info in files_response.content:
                    file_id = str(file_info.id)
                    processed_count += 1
                    
                    # 检查该文件是否在Label Studio中有对应的任务
                    task_id = dm_file_to_task_mapping.get(file_id)
                    if not task_id:
                        logger.debug(f"File {file_id} has no corresponding task in Label Studio, skipping")
                        skipped_count += 1
                        continue
                    
                    # 获取DataMate中的标注
                    dm_tags: List[Dict[str, Any]] = file_info.tags if file_info.tags else []  # type: ignore
                    
                    if not dm_tags:
                        logger.debug(f"File {file_id} has no annotations in DataMate, skipping")
                        skipped_count += 1
                        continue
                    
                    # 获取DataMate中标注的更新时间
                    dm_tags_updated_at: Optional[str] = None
                    if file_info.tags_updated_at:  # type: ignore
                        dm_tags_updated_at = file_info.tags_updated_at.isoformat()  # type: ignore
                    
                    try:
                        # 获取Label Studio中该任务的现有标注
                        ls_annotations = await self.ls_client.get_task_annotations(task_id)
                        
                        # 获取Label Studio标注的更新时间
                        ls_updated_at = ""
                        if ls_annotations:
                            latest_ls_annotation = max(
                                ls_annotations, 
                                key=lambda a: a.get("updated_at") or a.get("created_at", "")
                            )
                            ls_updated_at = latest_ls_annotation.get("updated_at") or latest_ls_annotation.get("created_at", "")
                        
                        # 检查是否应该覆盖Label Studio的标注
                        if not self._should_overwrite_ls(dm_tags_updated_at, ls_updated_at, overwrite_ls):
                            logger.debug(f"Task {task_id}: Label Studio has newer or equal annotations, skipping (overwrite_ls={overwrite_ls})")
                            skipped_count += 1
                            continue
                        
                        # 如果存在冲突，记录为冲突解决
                        if ls_annotations and dm_tags:
                            conflicts_resolved += 1
                            logger.debug(f"Task {task_id}: Resolved conflict, DataMate annotation is newer")
                        
                        # 将DataMate的标注转换为Label Studio格式
                        ls_result = []
                        for tag in dm_tags:
                            ls_result_item = {
                                "from_name": tag.get("from_name", ""),
                                "to_name": tag.get("to_name", ""),
                                "type": tag.get("type", ""),
                                "value": tag.get("values", {})
                            }
                            ls_result.append(ls_result_item)
                        
                        # 如果Label Studio已有标注，更新它；否则创建新标注
                        if ls_annotations:
                            # 更新最新的标注
                            latest_annotation_id = latest_ls_annotation.get("id")
                            if not latest_annotation_id:
                                logger.error(f"Task {task_id} has no annotation ID")
                                failed_count += 1
                                continue
                            
                            update_result = await self.ls_client.update_annotation(
                                int(latest_annotation_id),
                                ls_result
                            )
                            if update_result:
                                synced_count += 1
                                logger.debug(f"Updated annotation for task {task_id}")
                            else:
                                failed_count += 1
                                logger.error(f"Failed to update annotation for task {task_id}")
                        else:
                            # 创建新标注
                            create_result = await self.ls_client.create_annotation(
                                task_id,
                                ls_result
                            )
                            if create_result:
                                synced_count += 1
                                logger.debug(f"Created annotation for task {task_id}")
                            else:
                                failed_count += 1
                                logger.error(f"Failed to create annotation for task {task_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to sync annotations for file {file_id} (task {task_id}): {e}")
                        failed_count += 1
                
                # 检查是否还有更多页面
                if page >= files_response.totalPages - 1:
                    break
                page += 1
            
            logger.info(f"Annotation sync completed: synced={synced_count}, skipped={skipped_count}, failed={failed_count}, conflicts_resolved={conflicts_resolved}")
            
            status = "success" if failed_count == 0 else ("partial" if synced_count > 0 else "error")
            
            return SyncAnnotationsResponse(
                id=mapping.id,
                status=status,
                synced_to_dm=0,
                synced_to_ls=synced_count,
                skipped=skipped_count,
                failed=failed_count,
                conflicts_resolved=conflicts_resolved,
                message=f"Synced {synced_count} annotations from DataMate to Label Studio. Skipped: {skipped_count}, Failed: {failed_count}, Conflicts resolved: {conflicts_resolved}"
            )
            
        except Exception as e:
            logger.error(f"Error while syncing annotations from DM to LS: {e}")
            return SyncAnnotationsResponse(
                id=mapping.id,
                status="error",
                synced_to_dm=0,
                synced_to_ls=synced_count,
                skipped=skipped_count,
                failed=failed_count,
                conflicts_resolved=conflicts_resolved,
                message=f"Sync failed: {str(e)}"
            )
    
    async def sync_annotations_bidirectional(
        self,
        mapping: DatasetMappingResponse,
        batch_size: int = 50,
        overwrite: bool = True,
        overwrite_ls: bool = True
    ) -> SyncAnnotationsResponse:
        """
        双向同步标注结果
        
        Args:
            mapping: 数据集映射信息
            batch_size: 批处理大小
            overwrite: 是否允许覆盖DataMate中的标注
            overwrite_ls: 是否允许覆盖Label Studio中的标注
            
        Returns:
            同步结果响应
        """
        logger.info(f"Bidirectional annotation sync: dataset={mapping.dataset_id}, project={mapping.labeling_project_id}")
        
        try:
            # 先从Label Studio同步到DataMate
            ls_to_dm_result = await self.sync_annotations_from_ls_to_dm(
                mapping,
                batch_size,
                overwrite
            )
            
            # 再从DataMate同步到Label Studio
            dm_to_ls_result = await self.sync_annotations_from_dm_to_ls(
                mapping,
                batch_size,
                overwrite_ls
            )
            
            # 合并结果
            total_synced_to_dm = ls_to_dm_result.synced_to_dm
            total_synced_to_ls = dm_to_ls_result.synced_to_ls
            total_skipped = ls_to_dm_result.skipped + dm_to_ls_result.skipped
            total_failed = ls_to_dm_result.failed + dm_to_ls_result.failed
            total_conflicts = ls_to_dm_result.conflicts_resolved + dm_to_ls_result.conflicts_resolved
            
            # 判断状态
            if ls_to_dm_result.status == "error" and dm_to_ls_result.status == "error":
                status = "error"
            elif total_failed > 0:
                status = "partial"
            else:
                status = "success"
            
            logger.info(f"Bidirectional sync completed: to_dm={total_synced_to_dm}, to_ls={total_synced_to_ls}, skipped={total_skipped}, failed={total_failed}, conflicts={total_conflicts}")
            
            return SyncAnnotationsResponse(
                id=mapping.id,
                status=status,
                synced_to_dm=total_synced_to_dm,
                synced_to_ls=total_synced_to_ls,
                skipped=total_skipped,
                failed=total_failed,
                conflicts_resolved=total_conflicts,
                message=f"Bidirectional sync completed: {total_synced_to_dm} to DataMate, {total_synced_to_ls} to Label Studio. Skipped: {total_skipped}, Failed: {total_failed}, Conflicts resolved: {total_conflicts}"
            )
            
        except Exception as e:
            logger.error(f"Error during bidirectional sync: {e}")
            return SyncAnnotationsResponse(
                id=mapping.id,
                status="error",
                synced_to_dm=0,
                synced_to_ls=0,
                skipped=0,
                failed=0,
                conflicts_resolved=0,
                message=f"Bidirectional sync failed: {str(e)}"
            )
    
    async def get_sync_status(
        self, 
        dataset_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取同步状态"""
        mapping = await self.mapping_service.get_mapping_by_source_uuid(dataset_id)
        if not mapping:
            return None
        
        # 获取DM数据集信息
        dataset_info = await self.dm_client.get_dataset(dataset_id)
        
        # 获取Label Studio项目任务数量
        tasks_info = await self.ls_client.get_project_tasks(mapping.labeling_project_id)
        
        return {
            "id": mapping.id,
            "dataset_id": dataset_id,
            "labeling_project_id": mapping.labeling_project_id,
            "dm_total_files": dataset_info.fileCount if dataset_info else 0,
            "ls_total_tasks": tasks_info.get("count", 0) if tasks_info else 0,
            "sync_ratio": (
                tasks_info.get("count", 0) / dataset_info.fileCount 
                if dataset_info and dataset_info.fileCount > 0 and tasks_info else 0
            )
        }