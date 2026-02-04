"""
Operator Schemas
算子 Schema 定义
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.module.shared.schema import BaseResponseModel
from .release import OperatorReleaseDto


class OperatorDto(BaseResponseModel):
    """算子 DTO"""
    id: str = Field(..., description="算子ID")
    name: str = Field(..., description="算子名称")
    description: Optional[str] = Field(None, description="算子描述")
    version: str = Field(..., description="算子版本")
    inputs: Optional[str] = Field(None, description="输入定义（JSON）")
    outputs: Optional[str] = Field(None, description="输出定义（JSON）")
    runtime: Optional[str] = Field(None, description="运行时配置（JSON）")
    settings: Optional[str] = Field(None, description="算子设置（JSON）")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    metrics: Optional[str] = Field(None, description="算子指标（JSON）")
    usage_count: Optional[int] = Field(None, description="使用次数")
    is_star: Optional[bool] = Field(None, description="是否收藏")
    categories: Optional[List[str]] = Field(None, description="分类ID列表")
    overrides: Optional[Dict[str, Any]] = Field(None, description="设置覆盖值")
    requirements: Optional[List[str]] = Field(None, description="Python 依赖列表")
    readme: Optional[str] = Field(None, description="README 内容")
    releases: Optional[List[OperatorReleaseDto]] = Field(None, description="发布版本列表")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class OperatorListRequest(BaseResponseModel):
    """算子列表查询请求"""
    page: int = Field(1, ge=0, description="页码（从0开始）")
    size: int = Field(10, ge=1, description="页大小")
    categories: List[List[str]] = Field(default_factory=list, description="分类ID列表（每个父分类下的id放到一个列表中）")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    label_name: Optional[str] = Field(None, description="标签名称（暂不支持）")
    is_star: Optional[bool] = Field(None, description="是否收藏")


class PreUploadResponse(BaseResponseModel):
    """预上传响应"""
    req_id: str = Field(..., description="请求ID")


class OperatorUpdateDto(BaseResponseModel):
    """算子更新 DTO（所有字段可选）"""
    name: Optional[str] = Field(None, description="算子名称")
    description: Optional[str] = Field(None, description="算子描述")
    version: Optional[str] = Field(None, description="算子版本")
    inputs: Optional[str] = Field(None, description="输入定义（JSON）")
    outputs: Optional[str] = Field(None, description="输出定义（JSON）")
    runtime: Optional[str] = Field(None, description="运行时配置（JSON）")
    settings: Optional[str] = Field(None, description="算子设置（JSON）")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    metrics: Optional[str] = Field(None, description="算子指标（JSON）")
    usage_count: Optional[int] = Field(None, description="使用次数")
    is_star: Optional[bool] = Field(None, description="是否收藏")
    categories: Optional[List[str]] = Field(None, description="分类ID列表")
    overrides: Optional[Dict[str, Any]] = Field(None, description="设置覆盖值")
    requirements: Optional[List[str]] = Field(None, description="Python 依赖列表")
    readme: Optional[str] = Field(None, description="README 内容")
    releases: Optional[List[OperatorReleaseDto]] = Field(None, description="发布版本列表")
