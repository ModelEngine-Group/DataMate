from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DatasetTypeResponse(BaseModel):
    """数据集类型响应模型"""
    code: str = Field(..., description="类型编码")
    name: str = Field(..., description="类型名称")
    description: Optional[str] = Field(None, description="类型描述")
    supportedFormats: List[str] = Field(default_factory=list, description="支持的文件格式")
    icon: Optional[str] = Field(None, description="图标")

class DatasetResponse(BaseModel):
    """DM服务数据集响应模型"""
    id: str = Field(..., description="数据集ID")
    name: str = Field(..., description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    datasetType: str = Field(..., description="数据集类型", alias="datasetType")
    status: str = Field(..., description="数据集状态")
    fileCount: int = Field(..., description="文件数量")
    totalSize: int = Field(..., description="总大小（字节）")
    createdAt: Optional[datetime] = Field(None, description="创建时间")
    updatedAt: Optional[datetime] = Field(None, description="更新时间")
    createdBy: Optional[str] = Field(None, description="创建者")
    
    # 为了向后兼容，添加一个属性方法返回类型对象
    @property
    def type(self) -> DatasetTypeResponse:
        """兼容属性：返回类型对象"""
        return DatasetTypeResponse(
            code=self.datasetType,
            name=self.datasetType,
            description=None,
            supportedFormats=[],
            icon=None
        )