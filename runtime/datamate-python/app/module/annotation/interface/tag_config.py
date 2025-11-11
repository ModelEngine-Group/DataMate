from fastapi import APIRouter
from app.module.shared.schema import StandardResponse
from app.module.annotation.config.tag_config import LabelStudioTagConfig

router = APIRouter(prefix="/tags", tags=["annotation/tags"])

@router.get("/config", response_model=None)
async def get_tag_config():
    """
    获取所有Label Studio标签类型的配置（对象+控件），用于前端动态渲染。
    """
    config = LabelStudioTagConfig._config
    return StandardResponse(code=200, message="success", data=config)
