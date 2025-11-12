import httpx
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.logging import get_logger

from .schema import (
    LabelStudioProject, 
    LabelStudioCreateProjectRequest,
    LabelStudioCreateTaskRequest
)

logger = get_logger(__name__)

class Client:
    """Label Studio服务客户端
    
    使用 HTTP REST API 直接与 Label Studio 交互
    认证方式：使用 Authorization: Token {token} 头部进行认证
    """
    
    # 默认标注配置模板
    DEFAULT_LABEL_CONFIGS = {
        "image": """
        <View>
          <Image name="image" value="$image"/>
          <RectangleLabels name="label" toName="image">
            <Label value="Object" background="red"/>
          </RectangleLabels>
        </View>
        """,
        "text": """
        <View>
          <Text name="text" value="$text"/>
          <Choices name="sentiment" toName="text">
            <Choice value="positive"/>
            <Choice value="negative"/>
            <Choice value="neutral"/>
          </Choices>
        </View>
        """,
        "audio": """
        <View>
          <Audio name="audio" value="$audio"/>
          <AudioRegionLabels name="label" toName="audio">
            <Label value="Speech" background="red"/>
            <Label value="Noise" background="blue"/>
          </AudioRegionLabels>
        </View>
        """,
        "video": """
        <View>
          <Video name="video" value="$video"/>
          <VideoRegionLabels name="label" toName="video">
            <Label value="Action" background="red"/>
          </VideoRegionLabels>
        </View>
        """
    }
    
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """初始化 Label Studio 客户端
        
        Args:
            base_url: Label Studio 服务地址
            token: API Token（使用 Authorization: Token {token} 头部）
            timeout: 请求超时时间（秒）
        """
        self.base_url = (base_url or settings.label_studio_base_url).rstrip("/")
        self.token = token or settings.label_studio_user_token
        self.timeout = timeout
        
        if not self.token:
            raise ValueError("Label Studio API token is required")
        
        # 初始化 HTTP 客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type": "application/json"
            }
        )
        
        logger.debug(f"Label Studio client initialized: {self.base_url}")
    
    def get_label_config_by_type(self, data_type: str) -> str:
        """根据数据类型获取标注配置"""
        return self.DEFAULT_LABEL_CONFIGS.get(data_type.lower(), self.DEFAULT_LABEL_CONFIGS["image"])
    
    async def create_project(
        self, 
        title: str, 
        description: str = "", 
        label_config: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """创建Label Studio项目"""
        try:
            logger.debug(f"Creating Label Studio project: {title}")
            logger.debug(f"Label Studio URL: {self.base_url}/api/projects")
            
            project_data = {
                "title": title,
                "description": description,
                "label_config": label_config or "<View></View>"
            }
            
            response = await self.client.post("/api/projects", json=project_data)
            response.raise_for_status()
            
            project = response.json()
            project_id = project.get("id")
            
            if not project_id:
                raise Exception("Label Studio response does not contain project ID")
            
            logger.debug(f"Project created successfully, ID: {project_id}")
            return project
        
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Create project failed - HTTP {e.response.status_code}\n"
                f"URL: {e.request.url}\n"
                f"Response Headers: {dict(e.response.headers)}\n"
                f"Response Body: {e.response.text[:1000]}"  # First 1000 chars
            )
            return None
        except httpx.ConnectError as e:
            logger.error(
                f"Failed to connect to Label Studio at {self.base_url}\n"
                f"Error: {str(e)}\n"
                f"Possible causes:\n"
                f"  - Label Studio service is not running\n"
                f"  - Incorrect URL configuration\n"
                f"  - Network connectivity issue"
            )
            return None
        except httpx.TimeoutException as e:
            logger.error(f"Request to Label Studio timed out after {self.timeout}s: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error while creating Label Studio project: {str(e)}", exc_info=True)
            return None
    
    async def import_tasks(
        self,
        project_id: int,
        tasks: List[Dict[str, Any]],
        commit_to_project: bool = True,
        return_task_ids: bool = True
    ) -> Optional[Dict[str, Any]]:
        """批量导入任务到Label Studio项目"""
        try:
            logger.debug(f"Importing {len(tasks)} tasks into project {project_id}")
            
            response = await self.client.post(
                f"/api/projects/{project_id}/import",
                json=tasks,
                params={
                    "commit_to_project": str(commit_to_project).lower(),
                    "return_task_ids": str(return_task_ids).lower()
                }
            )
            response.raise_for_status()
            
            result = response.json()
            task_count = result.get("task_count", len(tasks))
            
            logger.debug(f"Tasks imported successfully: {task_count}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Import tasks failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while importing tasks: {e}")
            return None
    
    async def create_tasks_batch(
        self,
        project_id: str,
        tasks: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """批量创建任务的便利方法"""
        try:
            pid = int(project_id)
            return await self.import_tasks(pid, tasks)
        except ValueError as e:
            logger.error(f"Invalid project ID format: {project_id}, error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error while creating tasks in batch: {e}")
            return None
    
    async def create_task(
        self,
        project_id: str,
        data: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """创建单个任务"""
        try:
            task = {"data": data}
            if meta:
                task["meta"] = meta
            
            return await self.create_tasks_batch(project_id, [task])
            
        except Exception as e:
            logger.error(f"Error while creating single task: {e}")
            return None
    
    async def get_project_tasks(
        self,
        project_id: str,
        page: Optional[int] = None,
        page_size: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """获取项目任务信息
        
        Args:
            project_id: 项目ID
            page: 页码（从1开始）。如果为None，则获取所有任务
            page_size: 每页大小
            
        Returns:
            如果指定了page参数，返回包含分页信息的字典：
            {
                "count": 总任务数,
                "page": 当前页码,
                "page_size": 每页大小,
                "project_id": 项目ID,
                "tasks": 当前页的任务列表
            }
            
            如果page为None，返回包含所有任务的字典：
            
                "count": 总任务数,
                "project_id": 项目ID,
                "tasks": 所有任务列表
            }
        """
        try:
            pid = int(project_id)
            
            # 如果指定了page，直接获取单页任务
            if page is not None:
                logger.debug(f"Fetching tasks for project {pid}, page {page} (page_size={page_size})")
                
                response = await self.client.get(
                    f"/api/tasks",
                    params={
                        "project": pid,
                        "page": page,
                        "page_size": page_size
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 返回单页结果，包含分页信息
                return {
                    "count": result.get("total", len(result.get("tasks", []))),
                    "page": page,
                    "page_size": page_size,
                    "project_id": pid,
                    "tasks": result.get("tasks", [])
                }
            
            # 如果未指定page，获取所有任务
            logger.debug(f"(page) not specified, fetching all tasks.")
            all_tasks = []
        
            response = await self.client.get(
                f"/api/tasks",
                params={
                    "project": pid
                }
            )
            response.raise_for_status()
            
            result = response.json()
            tasks = result.get("tasks", [])
            
            if not tasks:
                logger.debug(f"No tasks found for this project.")

            
            all_tasks.extend(tasks)
            logger.debug(f"Fetched {len(tasks)} tasks.")
        
            # 返回所有任务，不包含分页信息
            return {
                "count": len(all_tasks),
                "project_id": pid,
                "tasks": all_tasks
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"获取项目任务失败 HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"获取项目任务时发生错误: {e}")
            return None
    
    async def delete_task(
        self,
        task_id: int
    ) -> bool:
        """删除单个任务"""
        try:
            logger.debug(f"Deleting task: {task_id}")
            
            response = await self.client.delete(f"/api/tasks/{task_id}")
            response.raise_for_status()
            
            logger.debug(f"Task deleted: {task_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Delete task {task_id} failed HTTP {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error while deleting task {task_id}: {e}")
            return False
    
    async def delete_tasks_batch(
        self,
        task_ids: List[int]
    ) -> Dict[str, int]:
        """批量删除任务"""
        try:
            logger.debug(f"Deleting {len(task_ids)} tasks in batch")
            
            successful_deletions = 0
            failed_deletions = 0
            
            for task_id in task_ids:
                if await self.delete_task(task_id):
                    successful_deletions += 1
                else:
                    failed_deletions += 1
            
            logger.debug(f"Batch deletion finished: success {successful_deletions}, failed {failed_deletions}")
            
            return {
                "successful": successful_deletions,
                "failed": failed_deletions,
                "total": len(task_ids)
            }
            
        except Exception as e:
            logger.error(f"Error while deleting tasks in batch: {e}")
            return {
                "successful": 0,
                "failed": len(task_ids),
                "total": len(task_ids)
            }
    
    async def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        try:
            logger.debug(f"Fetching project info: {project_id}")
            
            response = await self.client.get(f"/api/projects/{project_id}")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get project info failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while getting project info: {e}")
            return None
    
    async def delete_project(self, project_id: int) -> bool:
        """删除项目"""
        try:
            logger.debug(f"Deleting project: {project_id}")
            
            response = await self.client.delete(f"/api/projects/{project_id}")
            response.raise_for_status()
            
            logger.debug(f"Project deleted: {project_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Delete project {project_id} failed HTTP {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error while deleting project {project_id}: {e}")
            return False
    
    async def get_task_annotations(
        self,
        task_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """获取任务的标注结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            标注结果列表，每个标注包含完整的annotation信息
        """
        try:
            logger.debug(f"Fetching annotations for task: {task_id}")
            
            response = await self.client.get(f"/api/tasks/{task_id}/annotations")
            response.raise_for_status()
            
            annotations = response.json()
            logger.debug(f"Fetched {len(annotations)} annotations for task {task_id}")
            
            return annotations
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Get task annotations failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while getting task annotations: {e}")
            return None
    
    async def create_annotation(
        self,
        task_id: int,
        result: List[Dict[str, Any]],
        completed_by: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """为任务创建新的标注
        
        Args:
            task_id: 任务ID
            result: 标注结果列表
            completed_by: 完成标注的用户ID（可选）
            
        Returns:
            创建的标注信息，失败返回None
        """
        try:
            logger.debug(f"Creating annotation for task: {task_id}")
            
            annotation_data = {
                "result": result,
                "task": task_id
            }
            
            if completed_by:
                annotation_data["completed_by"] = completed_by
            
            response = await self.client.post(
                f"/api/tasks/{task_id}/annotations",
                json=annotation_data
            )
            response.raise_for_status()
            
            annotation = response.json()
            logger.debug(f"Created annotation {annotation.get('id')} for task {task_id}")
            
            return annotation
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Create annotation failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while creating annotation: {e}")
            return None
    
    async def update_annotation(
        self,
        annotation_id: int,
        result: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """更新已存在的标注
        
        Args:
            annotation_id: 标注ID
            result: 新的标注结果列表
            
        Returns:
            更新后的标注信息，失败返回None
        """
        try:
            logger.debug(f"Updating annotation: {annotation_id}")
            
            annotation_data = {
                "result": result
            }
            
            response = await self.client.patch(
                f"/api/annotations/{annotation_id}",
                json=annotation_data
            )
            response.raise_for_status()
            
            annotation = response.json()
            logger.debug(f"Updated annotation {annotation_id}")
            
            return annotation
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Update annotation failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while updating annotation: {e}")
            return None
    
    async def delete_annotation(
        self,
        annotation_id: int
    ) -> bool:
        """删除标注
        
        Args:
            annotation_id: 标注ID
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            logger.debug(f"Deleting annotation: {annotation_id}")
            
            response = await self.client.delete(f"/api/annotations/{annotation_id}")
            response.raise_for_status()
            
            logger.debug(f"Deleted annotation {annotation_id}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Delete annotation failed HTTP {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error while deleting annotation: {e}")
            return False
    
    async def create_local_storage(
        self,
        project_id: int,
        path: str,
        title: str,
        use_blob_urls: bool = True,
        regex_filter: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """创建本地文件存储配置
        
        Args:
            project_id: Label Studio 项目 ID
            path: 本地文件路径（在 Label Studio 容器中的路径）
            title: 存储配置标题
            use_blob_urls: 是否使用 blob URLs（建议 True）
            regex_filter: 文件过滤正则表达式（可选）
            description: 存储描述（可选）
            
        Returns:
            创建的存储配置信息，失败返回 None
        """
        try:
            logger.debug(f"Creating local storage for project {project_id}: {path}")
            
            storage_data = {
                "project": project_id,
                "path": path,
                "title": title,
                "use_blob_urls": use_blob_urls
            }
            
            if regex_filter:
                storage_data["regex_filter"] = regex_filter
            if description:
                storage_data["description"] = description
            
            response = await self.client.post(
                "/api/storages/localfiles/",
                json=storage_data
            )
            response.raise_for_status()
            
            storage = response.json()
            storage_id = storage.get("id")
            
            logger.debug(f"Local storage created successfully, ID: {storage_id}")
            return storage
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Create local storage failed HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error while creating local storage: {e}")
            return None

    async def close(self):
        """关闭客户端连接"""
        try:
            await self.client.aclose()
            logger.debug("Label Studio client closed")
        except Exception as e:
            logger.error(f"Error while closing Label Studio client: {e}")
