"""
System Parameter DTOs
系统参数数据传输对象
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.module.shared.schema import BaseResponseModel


class SysParamDto(BaseResponseModel):
    """系统参数 DTO"""

    id: str = Field(..., description="参数ID")
    param_value: str = Field(..., description="参数值")
    param_type: str = Field(
        default="string", description="参数类型（string、integer、boolean）"
    )
    option_list: Optional[str] = Field(None, description="选项列表（JSON格式）")
    description: Optional[str] = Field(None, description="参数描述")
    is_built_in: bool = Field(default=False, description="是否内置")
    can_modify: bool = Field(default=True, description="是否可修改")
    is_enabled: bool = Field(default=True, description="是否启用")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")

    class Config:
        from_attributes = True


class UpdateParamValueRequest(BaseResponseModel):
    """更新参数值请求"""

    param_value: str = Field(..., description="参数值")


class CreateSysParamRequest(BaseResponseModel):
    """创建系统参数请求"""

    id: str = Field(..., description="参数ID")
    param_value: str = Field(..., description="参数值")
    param_type: str = Field(default="string", description="参数类型")
    option_list: Optional[str] = Field(None, description="选项列表（JSON格式）")
    description: Optional[str] = Field(None, description="参数描述")
    is_built_in: bool = Field(default=False, description="是否内置")
    can_modify: bool = Field(default=True, description="是否可修改")
    is_enabled: bool = Field(default=True, description="是否启用")
