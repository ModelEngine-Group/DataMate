from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings
from app.module.shared.schema import StandardResponse

from ..schema import HealthResponse

router = APIRouter()

@router.get("/health", response_model=StandardResponse[HealthResponse])
async def health_check():
    """健康检查端点"""

    return StandardResponse(
        code="0",
        message="success",
        data=HealthResponse(
            status="healthy",
            service="Label Studio Adapter",
            version=settings.app_version
        )
    )