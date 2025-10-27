from typing import Optional, List, Dict, Any, Tuple
from app.infrastructure import LabelStudioClient, DatamateClient
from app.services.dataset_mapping_service import DatasetMappingService
from app.schemas.dataset_mapping import SyncDatasetResponse
from app.core.logging import get_logger
from app.core.config import settings
from app.exceptions import NoDatasetInfoFoundError, DatasetMappingNotFoundError

logger = get_logger(__name__)

class SyncService:
    """数据同步服务"""
    
    def __init__(
        self, 
        dm_client: DatamateClient, 
        ls_client: LabelStudioClient,
        mapping_service: DatasetMappingService
    ):
        self.dm_client = dm_client
        self.ls_client = ls_client
        self.mapping_service = mapping_service
    
    def determine_data_type(self, file_type: str) -> str:
        """根据文件类型确定数据类型"""
        file_type_lower = file_type.lower()
        
        if any(ext in file_type_lower for ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']):
            return 'image'
        elif any(ext in file_type_lower for ext in ['mp3', 'wav', 'flac', 'aac', 'ogg']):
            return 'audio'
        elif any(ext in file_type_lower for ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']):
            return 'video'
        elif any(ext in file_type_lower for ext in ['txt', 'doc', 'docx', 'pdf']):
            return 'text'
        else:
            return 'image'  # 默认为图像类型
    
    async def get_existing_dm_file_mapping(self, project_id: str) -> Dict[str, int]:
        """
        获取Label Studio项目中已存在的DM文件ID到任务ID的映射
        
        Args:
            project_id: Label Studio项目ID
            
        Returns:
            dm_file_id到task_id的映射字典
        """
        try:
            logger.info(f"Fetching existing task mappings for project {project_id} (page_size={settings.ls_task_page_size})")
            dm_file_to_task_mapping = {}

            # 使用Label Studio客户端封装的方法获取所有任务
            page_size = getattr(settings, 'ls_task_page_size', 1000)
            
            # 调用封装好的方法获取所有任务，page=None表示获取全部
            result = await self.ls_client.get_project_tasks(
                project_id=project_id,
                page=None,  # 不指定page，获取所有任务
                page_size=page_size
            )
            
            if not result:
                logger.warning(f"Failed to fetch tasks for project {project_id}")
                return {}
            
            all_tasks = result.get("tasks", [])

            # 遍历所有任务，构建映射
            for task in all_tasks:
                # 检查任务的meta字段中是否有dm_file_id
                meta = task.get('meta')
                if meta:
                    dm_file_id = meta.get('dm_file_id')
                    if dm_file_id:
                        task_id = task.get('id')
                        if task_id:
                            dm_file_to_task_mapping[str(dm_file_id)] = task_id

            logger.info(f"Found {len(dm_file_to_task_mapping)} existing task mappings")
            return dm_file_to_task_mapping

        except Exception as e:
            logger.error(f"Error while fetching existing tasks: {e}")
            return {}  # 发生错误时返回空字典，会同步所有文件
    
    async def sync_dataset_files(
        self, 
        mapping_id: str, 
        batch_size: int = 50
    ) -> SyncDatasetResponse:
        """同步数据集文件到Label Studio"""
        logger.info(f"Start syncing dataset by mapping: {mapping_id}")
        
        # 获取映射关系
        mapping = await self.mapping_service.get_mapping_by_uuid(mapping_id)
        if not mapping:
            logger.error(f"Dataset mapping not found: {mapping_id}")
            return SyncDatasetResponse(
                mapping_id="",
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Dataset mapping not found: {mapping_id}"
            )
        
        try:
            # 获取数据集信息
            dataset_info = await self.dm_client.get_dataset(mapping.dataset_id)
            if not dataset_info:
                raise NoDatasetInfoFoundError(mapping.dataset_id)
            
            synced_files = 0
            deleted_tasks = 0
            total_files = dataset_info.fileCount
            page = 0
            
            logger.info(f"Total files in dataset: {total_files}")
            
            # 获取Label Studio中已存在的DM文件ID到任务ID的映射
            existing_dm_file_mapping = await self.get_existing_dm_file_mapping(mapping.labelling_project_id)
            existing_dm_file_ids = set(existing_dm_file_mapping.keys())
            logger.info(f"{len(existing_dm_file_ids)} tasks already exist in Label Studio")
            
            # 收集DM中当前存在的所有文件ID
            current_dm_file_ids = set()
            
            # 分页获取并同步文件
            while True:
                files_response = await self.dm_client.get_dataset_files(
                    mapping.dataset_id, 
                    page=page, 
                    size=batch_size,
                    status="COMPLETED"  # 只同步已完成的文件
                )
                
                if not files_response or not files_response.content:
                    logger.info(f"No more files on page {page + 1}")
                    break
                
                logger.info(f"Processing page {page + 1}, total {len(files_response.content)} files")
                
                # 筛选出新文件并批量创建任务
                tasks = []
                new_files_count = 0
                existing_files_count = 0
                
                for file_info in files_response.content:
                    # 记录当前DM中存在的文件ID
                    current_dm_file_ids.add(str(file_info.id))
                    
                    # 检查文件是否已存在
                    if str(file_info.id) in existing_dm_file_ids:
                        existing_files_count += 1
                        logger.debug(f"Skip existing file: {file_info.originalName} (ID: {file_info.id})")
                        continue
                    
                    new_files_count += 1
                    
                    # 确定数据类型
                    data_type = self.determine_data_type(file_info.fileType)
                    
                    # 替换文件路径前缀:只替换开头的前缀，不影响路径中间可能出现的相同字符串
                    file_path = file_info.filePath.removeprefix(settings.dm_file_path_prefix)
                    file_path = settings.label_studio_file_path_prefix + file_path
                    
                    # 构造任务数据
                    task_data = {
                        "data": {
                            data_type: file_path
                        },
                        "meta": {
                            "file_size": file_info.size,
                            "file_type": file_info.fileType,
                            "dm_dataset_id": mapping.dataset_id,
                            "dm_file_id": file_info.id,
                            "original_name": file_info.originalName,
                        }
                    }
                    tasks.append(task_data)
                
                logger.info(f"Page {page + 1}: new files {new_files_count}, existing files {existing_files_count}")
                
                # 批量创建Label Studio任务
                if tasks:
                    batch_result = await self.ls_client.create_tasks_batch(
                        mapping.labelling_project_id,
                        tasks
                    )
                    
                    if batch_result:
                        synced_files += len(tasks)
                        logger.info(f"Successfully synced {len(tasks)} files")
                    else:
                        logger.warning(f"Batch task creation failed, fallback to single creation")
                        # 如果批量创建失败，尝试单个创建
                        for task_data in tasks:
                            task_result = await self.ls_client.create_task(
                                mapping.labelling_project_id,
                                task_data["data"],
                                task_data.get("meta")
                            )
                            if task_result:
                                synced_files += 1
                
                # 检查是否还有更多页面
                if page >= files_response.totalPages - 1:
                    break
                page += 1
            
            # 清理在DM中不存在但在Label Studio中存在的任务
            tasks_to_delete = []
            for dm_file_id, task_id in existing_dm_file_mapping.items():
                if dm_file_id not in current_dm_file_ids:
                    tasks_to_delete.append(task_id)
                    logger.debug(f"Mark task for deletion: {task_id} (DM file ID: {dm_file_id})")
            
            if tasks_to_delete:
                logger.info(f"Deleting {len(tasks_to_delete)} tasks not present in DM")
                delete_result = await self.ls_client.delete_tasks_batch(tasks_to_delete)
                deleted_tasks = delete_result.get("successful", 0)
                logger.info(f"Successfully deleted {deleted_tasks} tasks")
            else:
                logger.info("No tasks to delete")
            
            # 更新映射的最后更新时间
            await self.mapping_service.update_last_updated_at(mapping.mapping_id)
            
            logger.info(f"Sync completed: total_files={total_files}, created={synced_files}, deleted={deleted_tasks}")
            
            return SyncDatasetResponse(
                mapping_id=mapping.mapping_id,
                status="success",
                synced_files=synced_files,
                total_files=total_files,
                message=f"Sync completed: created {synced_files} files, deleted {deleted_tasks} tasks"
            )
            
        except Exception as e:
            logger.error(f"Error while syncing dataset: {e}")
            return SyncDatasetResponse(
                mapping_id=mapping.mapping_id,
                status="error",
                synced_files=0,
                total_files=0,
                message=f"Sync failed: {str(e)}"
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
        tasks_info = await self.ls_client.get_project_tasks(mapping.labelling_project_id)
        
        return {
            "mapping_id": mapping.mapping_id,
            "dataset_id": dataset_id,
            "labelling_project_id": mapping.labelling_project_id,
            "last_updated_at": mapping.last_updated_at,
            "dm_total_files": dataset_info.fileCount if dataset_info else 0,
            "ls_total_tasks": tasks_info.get("count", 0) if tasks_info else 0,
            "sync_ratio": (
                tasks_info.get("count", 0) / dataset_info.fileCount 
                if dataset_info and dataset_info.fileCount > 0 and tasks_info else 0
            )
        }