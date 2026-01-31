"""
Operator Release Schemas
算子发布版本 Schema 定义
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.module.shared.schema import BaseResponseModel


class OperatorReleaseDto(BaseResponseModel):
    """算子发布版本 DTO"""
    id: str = Field(..., description="算子ID")
    version: str = Field(..., description="版本号")
    release_date: Optional[datetime] = Field(None, description="发布时间")
    changelog: Optional[List[str]] = Field(None, description="更新日志列表")


__all__ = ["OperatorReleaseDto"]
