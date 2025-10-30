from pydantic import Field
from typing import Optional
from datetime import datetime

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse

class _DatasetMappingBase(BaseResponseModel):
    """数据集映射 基础模型"""
    dataset_id: str = Field(..., description="源数据集ID")

class DatasetMappingCreateRequest(_DatasetMappingBase):
    """数据集映射 创建 请求模型"""
    pass

class DatasetMappingCreateResponse(BaseResponseModel):
    """数据集映射 创建 响应模型"""
    id: str = Field(..., description="映射UUID")
    labeling_project_id: str = Field(..., description="Label Studio项目ID")
    labeling_project_name: str = Field(..., description="Label Studio项目名称")

class DatasetMappingUpdateRequest(BaseResponseModel):
    """数据集映射 更新 请求模型"""
    dataset_id: Optional[str] = Field(None, description="源数据集ID")

class DatasetMappingResponse(_DatasetMappingBase):
    """数据集映射 查询 响应模型"""
    id: str = Field(..., description="映射UUID")
    labeling_project_id: str = Field(..., description="标注项目ID")
    name: Optional[str] = Field(None, description="标注项目名称")
    created_at: datetime = Field(..., description="创建时间")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        
class DeleteDatasetResponse(BaseResponseModel):
    """删除数据集响应模型"""
    id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="删除状态")