from pydantic import Field

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse

class ConfigResponse(BaseResponseModel):
    """配置信息响应模型"""
    label_studio_url: str = Field(..., description="Label Studio基础URL")