from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings
from app.schemas import StandardResponse

router = APIRouter()

@router.get("/health", response_model=StandardResponse[Dict[str, Any]])
async def health_check():
    """健康检查端点"""
    return StandardResponse(
        code=200,
        message="success",
        data={
            "status": "healthy",
            "service": "Label Studio Adapter",
            "version": settings.app_version
        }
    )

@router.get("/config", response_model=StandardResponse[Dict[str, Any]])
async def get_config():
    """获取配置信息"""
    return StandardResponse(
        code=200,
        message="success",
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "dm_service_url": settings.dm_service_base_url,
            "label_studio_url": settings.label_studio_base_url,
            "debug": settings.debug
        }
    )