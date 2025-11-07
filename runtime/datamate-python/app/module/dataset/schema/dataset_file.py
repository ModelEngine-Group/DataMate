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
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="文件标签/标注信息")
    tags_updated_at: Optional[datetime] = Field(None, description="标签最后更新时间", alias="tagsUpdatedAt")

class PagedDatasetFileResponse(BaseModel):
    """DM服务分页文件响应模型"""
    content: List[DatasetFileResponse] = Field(..., description="文件列表")
    totalElements: int = Field(..., description="总元素数")
    totalPages: int = Field(..., description="总页数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    
