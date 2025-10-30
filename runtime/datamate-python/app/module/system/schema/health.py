from pydantic import Field

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse

class HealthResponse(BaseResponseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="应用版本")