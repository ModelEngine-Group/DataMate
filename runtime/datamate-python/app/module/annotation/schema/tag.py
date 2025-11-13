from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from app.module.shared.schema import BaseResponseModel

class UpdateFileTagsRequest(BaseModel):
    """更新文件标签请求"""
    tags: List[Dict[str, Any]] = Field(..., description="要更新的标签列表（部分更新）")
    

class UpdateFileTagsResponse(BaseResponseModel):
    """更新文件标签响应"""
    file_id: str = Field(..., alias="fileId", description="文件ID")
    tags: List[Dict[str, Any]] = Field(..., description="更新后的完整标签列表")
    tags_updated_at: datetime = Field(..., alias="tagsUpdatedAt", description="标签更新时间")
    