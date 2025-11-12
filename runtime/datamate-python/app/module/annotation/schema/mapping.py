from pydantic import Field, BaseModel
from typing import Optional
from datetime import datetime

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse


class DatasetMappingCreateRequest(BaseModel):
    """数据集映射 创建 请求模型

    Accept both snake_case and camelCase field names from frontend JSON by
    declaring explicit aliases. Frontend sends `datasetId`, `name`,
    `description`, `templateId` (camelCase), so provide aliases so pydantic will map them
    to the internal attributes used in the service code (dataset_id, name,
    description, template_id).
    """
    dataset_id: str = Field(..., alias="datasetId", description="源数据集ID")
    name: Optional[str] = Field(None, alias="name", description="标注项目名称")
    description: Optional[str] = Field(None, alias="description", description="标注项目描述")
    template_id: Optional[str] = Field(None, alias="templateId", description="标注模板ID")

    class Config:
        # allow population by field name when constructing model programmatically
        validate_by_name = True

class DatasetMappingCreateResponse(BaseResponseModel):
    """数据集映射 创建 响应模型"""
    id: str = Field(..., description="映射UUID")
    labeling_project_id: str = Field(..., description="Label Studio项目ID")
    labeling_project_name: str = Field(..., description="Label Studio项目名称")

class DatasetMappingUpdateRequest(BaseResponseModel):
    """数据集映射 更新 请求模型"""
    dataset_id: Optional[str] = Field(None, description="源数据集ID")

class DatasetMappingResponse(BaseModel):
    """数据集映射 查询 响应模型"""
    id: str = Field(..., description="映射UUID")
    dataset_id: str = Field(..., alias="datasetId", description="源数据集ID")
    dataset_name: Optional[str] = Field(None, alias="datasetName", description="数据集名称")
    labeling_project_id: str = Field(..., alias="labelingProjectId", description="标注项目ID")
    name: Optional[str] = Field(None, description="标注项目名称")
    description: Optional[str] = Field(None, description="标注项目描述")
    created_at: datetime = Field(..., alias="createdAt", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="更新时间")
    deleted_at: Optional[datetime] = Field(None, alias="deletedAt", description="删除时间")
    
    class Config:
        from_attributes = True
        populate_by_name = True
        
class DeleteDatasetResponse(BaseResponseModel):
    """删除数据集响应模型"""
    id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="删除状态")