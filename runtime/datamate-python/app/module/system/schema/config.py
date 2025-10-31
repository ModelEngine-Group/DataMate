from pydantic import Field

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse

class ConfigResponse(BaseResponseModel):
    """配置信息响应模型"""
    app_name: str = Field(..., description="应用名称")
    version: str = Field(..., description="应用版本")
    label_studio_url: str = Field(..., description="Label Studio基础URL")
    debug: bool = Field(..., description="调试模式状态")