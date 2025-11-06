from typing import Optional, List, Dict, Any, Tuple, Set
from app.module.dataset import DatasetManagementService

from app.core.logging import get_logger
from app.core.config import settings
from app.exception import NoDatasetInfoFoundError

from ..client import LabelStudioClient
from ..schema import (
    SyncDatasetResponse,
    DatasetMappingResponse
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