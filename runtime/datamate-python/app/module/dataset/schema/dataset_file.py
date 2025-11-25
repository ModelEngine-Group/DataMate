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

class DatasetFileTag(BaseModel):
    id: str = Field(None, description="标签ID")
    type: str = Field(None, description="类型")
    from_name: str = Field(None, description="标签名称")
    values: dict = Field(None, description="标签值")

    def get_tags(self) -> List[str]:
        tags = []
        # 如果 values 是字典类型，根据 type 获取对应的值
        tag_values = self.values.get(self.type, [])

        # 处理标签值
        if isinstance(tag_values, list):
            for tag in tag_values:
                if isinstance(tag, str):
                    tags.append(str(tag))
        elif isinstance(tag_values, str):
            tags.append(tag_values)
        # 如果 from_name 不为空，添加前缀
        if self.from_name:
            tags = [f"{self.from_name}@{tag}" for tag in tags]
        return tags


class FileTagUpdate(BaseModel):
    """单个文件的标签更新请求"""
    file_id: str = Field(..., alias="fileId", description="文件ID")
    tags: List[Dict[str, Any]] = Field(..., description="要更新的标签列表（部分更新）")

    class Config:
        populate_by_name = True


class BatchUpdateFileTagsRequest(BaseModel):
    """批量更新文件标签请求"""
    updates: List[FileTagUpdate] = Field(..., description="文件标签更新列表", min_length=1)

    class Config:
        populate_by_name = True


class FileTagUpdateResult(BaseModel):
    """单个文件标签更新结果"""
    file_id: str = Field(..., alias="fileId", description="文件ID")
    success: bool = Field(..., description="是否更新成功")
    message: Optional[str] = Field(None, description="结果信息")
    tags_updated_at: Optional[datetime] = Field(None, alias="tagsUpdatedAt", description="标签更新时间")

    class Config:
        populate_by_name = True


class BatchUpdateFileTagsResponse(BaseModel):
    """批量更新文件标签响应"""
    results: List[FileTagUpdateResult] = Field(..., description="更新结果列表")
    total: int = Field(..., description="总更新数量")
    success_count: int = Field(..., alias="successCount", description="成功数量")
    failure_count: int = Field(..., alias="failureCount", description="失败数量")

    class Config:
        populate_by_name = True
