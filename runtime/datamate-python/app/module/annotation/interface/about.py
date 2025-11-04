from fastapi import APIRouter

from app.module.shared.schema import StandardResponse
from app.core.logging import get_logger
from app.core.config import settings

from ..schema import ConfigResponse


router = APIRouter(
    prefix="/about",
    tags=["annotation/about"]
)
logger = get_logger(__name__)

@router.get("", response_model=StandardResponse[ConfigResponse])
async def get_config():
    """获取配置信息"""
    return StandardResponse(
        code=200,
        message="success",
        data=ConfigResponse(
            label_studio_url=settings.label_studio_base_url,
        )
    )