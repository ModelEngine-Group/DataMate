from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DatasetFileResponse(BaseModel):
    """DM服务数据集文件响应模型"""
    id: str = Field(..., description="文件ID")
    fileName: str = Field(..., description="文件名")
    fileType: str = Field(..., description="文件类型")
    filePath: str = Field(..., description="文件路径")
    originalName: Optional[str] = Field(None, description="原始文件名")
    size: Optional[int] = Field(None, description="文件大小（字节）")
    status: Optional[str] = Field(None, description="文件状态")
    uploadedAt: Optional[datetime] = Field(None, description="上传时间")
    description: Optional[str] = Field(None, description="文件描述")
    uploadedBy: Optional[str] = Field(None, description="上传者")
    lastAccessTime: Optional[datetime] = Field(None, description="最后访问时间")

class PagedDatasetFileResponse(BaseModel):
    """DM服务分页文件响应模型"""
    content: List[DatasetFileResponse] = Field(..., description="文件列表")
    totalElements: int = Field(..., description="总元素数")
    totalPages: int = Field(..., description="总页数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    
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