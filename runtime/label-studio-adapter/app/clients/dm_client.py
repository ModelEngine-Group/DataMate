import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.dm_service import DatasetResponse, PagedDatasetFileResponse

logger = get_logger(__name__)

class DMServiceClient:
    """数据管理服务客户端"""
    
    def __init__(self, base_url: str|None = None, timeout: float = 30.0):
        self.base_url = base_url or settings.dm_service_base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )
        logger.info(f"Initialize DM service client, base url: {self.base_url}")

    @staticmethod
    def _unwrap_payload(data):
        """Unwrap common envelope shapes like {'code': ..., 'message': ..., 'data': {...}}."""
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], (dict, list)):
            return data['data']
        return data

    @staticmethod
    def _is_error_payload(data) -> bool:
        """Detect error-shaped payloads returned with HTTP 200."""
        if not isinstance(data, dict):
            return False
        # Common patterns: {error, message, ...} or {code, message, ...} without data
        if 'error' in data and 'message' in data:
            return True
        if 'code' in data and 'message' in data and 'data' not in data:
            return True
        return False

    @staticmethod
    def _keys(d):
        return list(d.keys()) if isinstance(d, dict) else []
    
    async def get_dataset(self, dataset_id: str) -> Optional[DatasetResponse]:
        """获取数据集详情"""
        try:
            logger.info(f"Getting dataset detail: {dataset_id} ...")
            response = await self.client.get(f"/data-management/datasets/{dataset_id}")
            response.raise_for_status()
            raw = response.json()

            data = self._unwrap_payload(raw)

            if self._is_error_payload(data):
                logger.error(f"DM service returned error for dataset {dataset_id}: {data}")
                return None
            if not isinstance(data, dict):
                logger.error(f"Unexpected dataset payload type for {dataset_id}: {type(data).__name__}")
                return None
            required = ["id", "name", "description", "datasetType", "status", "fileCount", "totalSize"]
            if not all(k in data for k in required):
                logger.error(f"Dataset payload missing required fields for {dataset_id}. Keys: {self._keys(data)}")
                return None
            return DatasetResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to get dataset {dataset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Unexpected] [GET] dataset {dataset_id}: \n{e}\nRaw JSON received: \n{raw}")

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
            params: dict = {"page": page, "size": size}
            if file_type:
                params["fileType"] = file_type
            if status:
                params["status"] = status
                
            response = await self.client.get(
                f"/data-management/datasets/{dataset_id}/files",
                params=params
            )
            response.raise_for_status()
            raw = response.json()
            data = self._unwrap_payload(raw)
            if self._is_error_payload(data):
                logger.error(f"DM service returned error for dataset files {dataset_id}: {data}")
                return None
            if not isinstance(data, dict):
                logger.error(f"Unexpected dataset files payload type for {dataset_id}: {type(data).__name__}")
                return None
            required = ["content", "totalElements", "totalPages", "page", "size"]
            if not all(k in data for k in required):
                logger.error(f"Files payload missing required fields for {dataset_id}. Keys: {self._keys(data)}")
                return None
            return PagedDatasetFileResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"Failed to get dataset files for {dataset_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"[Unexpected] [GET] dataset files {dataset_id}: \n{e}\nRaw JSON received: \n{raw}")
            return None
    
    async def download_file(self, dataset_id: str, file_id: str) -> Optional[bytes]:
        """下载文件内容"""
        try:
            logger.info(f"Download file: dataset={dataset_id}, file={file_id}")
            response = await self.client.get(
                f"/data-management/datasets/{dataset_id}/files/{file_id}/download"
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while downloading file {file_id}: {e}")
            return None
    
    async def get_file_download_url(self, dataset_id: str, file_id: str) -> str:
        """获取文件下载URL"""
        return f"{self.base_url}/data-management/datasets/{dataset_id}/files/{file_id}/download"
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
        logger.info("DM service client connection closed")