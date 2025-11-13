from fastapi import APIRouter

from app.module.shared.schema import StandardResponse
from app.core.logging import get_logger
from app.core.config import settings

from ..schema import (
    ConfigResponse,
    TagConfigResponse
)
from ..config.tag_config import LabelStudioTagConfig

router = APIRouter(
    prefix="/tags",
    tags=["annotation/config"]
)
logger = get_logger(__name__)

@router.get("", response_model=StandardResponse[ConfigResponse])
async def get_config():
    """获取配置信息（已废弃，请使用 /api/annotation/about）"""
    return StandardResponse(
        code=200,
        message="success",
        data=ConfigResponse(
            label_studio_url=settings.label_studio_base_url,
        )
    )

@router.get("/config", response_model=StandardResponse[TagConfigResponse], summary="获取标签配置")
async def get_tag_config():
    """
    获取所有Label Studio标签类型的配置（对象+控件），用于前端动态渲染。
    """
    # Ensure config is loaded by instantiating the class
    tag_config = LabelStudioTagConfig()
    config = LabelStudioTagConfig._config
    
    if not config:
        logger.error("Failed to load tag configuration")
        return StandardResponse(
            code=500, 
            message="Failed to load tag configuration",
            data={"objects": {}, "controls": {}}
        )
    
    return StandardResponse(code=200, message="success", data=config)
