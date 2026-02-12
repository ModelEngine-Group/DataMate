import httpx
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class RuntimeClient:
    """HTTP client for communicating with runtime service"""

    def __init__(self, base_url: str = "http://datamate-runtime:8081"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def submit_task(self, task_id: str) -> bool:
        """Submit cleaning task to runtime executor"""
        try:
            url = f"{self.base_url}/api/task/{task_id}/submit"
            response = await self.client.post(url)
            response.raise_for_status()
            logger.info(f"Task {task_id} submitted successfully")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to submit task {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error submitting task {task_id}: {e}")
            return False

    async def stop_task(self, task_id: str) -> bool:
        """Stop running cleaning task"""
        try:
            url = f"{self.base_url}/api/task/{task_id}/stop"
            response = await self.client.post(url)
            response.raise_for_status()
            logger.info(f"Task {task_id} stopped successfully")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to stop task {task_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error stopping task {task_id}: {e}")
            return False

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status from runtime"""
        try:
            url = f"{self.base_url}/api/task/{task_id}/status"
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting task status {task_id}: {e}")
            return None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
