from pydantic import Field
from typing import Optional
from datetime import datetime

from .common import BaseResponseModel

class DatasetMappingBase(BaseResponseModel):
    """数据集映射 基础模型"""
    source_dataset_id: str = Field(..., description="源数据集ID")

class DatasetMappingCreateRequest(DatasetMappingBase):
    """数据集映射 创建 请求模型"""
    pass

class DatasetMappingCreateResponse(BaseResponseModel):
    """数据集映射 创建 响应模型"""
    mapping_id: str = Field(..., description="映射UUID")
    labelling_project_id: str = Field(..., description="Label Studio项目ID")
    labelling_project_name: str = Field(..., description="Label Studio项目名称")
    message: str = Field(..., description="响应消息")

class DatasetMappingUpdateRequest(BaseResponseModel):
    """数据集映射 更新 请求模型"""
    source_dataset_id: Optional[str] = Field(None, description="源数据集ID")

class DatasetMappingResponse(DatasetMappingBase):
    """数据集映射 查询 响应模型"""
    mapping_id: str = Field(..., description="映射UUID")
    labelling_project_id: str = Field(..., description="标注项目ID")
    labelling_project_name: Optional[str] = Field(None, description="标注项目名称")
    created_at: datetime = Field(..., description="创建时间")
    last_updated_at: datetime = Field(..., description="最后更新时间")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class SyncDatasetRequest(BaseResponseModel):
    """同步数据集请求模型"""
    mapping_id: str = Field(..., description="映射ID（mapping UUID）")
    batch_size: int = Field(50, ge=1, le=100, description="批处理大小")

class SyncDatasetResponse(BaseResponseModel):
    """同步数据集响应模型"""
    mapping_id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="同步状态")
    synced_files: int = Field(..., description="已同步文件数量")
    total_files: int = Field(0, description="总文件数量")
    message: str = Field(..., description="响应消息")

class DeleteDatasetResponse(BaseResponseModel):
    """删除数据集响应模型"""
    mapping_id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="删除状态")
    message: str = Field(..., description="响应消息")