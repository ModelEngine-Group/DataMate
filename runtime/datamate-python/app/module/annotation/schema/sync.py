from pydantic import Field

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse


class SyncDatasetRequest(BaseResponseModel):
    """同步数据集请求模型"""
    id: str = Field(..., description="映射ID（mapping UUID）")
    batch_size: int = Field(50, ge=1, le=100, description="批处理大小")

class SyncDatasetResponse(BaseResponseModel):
    """同步数据集响应模型"""
    id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="同步状态")
    synced_files: int = Field(..., description="已同步文件数量")
    total_files: int = Field(0, description="总文件数量")
    message: str = Field(..., description="响应消息")

class SyncDatasetResponseStd(StandardResponse[SyncDatasetResponse]):
    pass