"""
模型配置 DTO：与 Java 版 t_models 接口保持一致。
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelType(str, Enum):
    """模型类型枚举，与 Java ModelType 一致。"""
    CHAT = "CHAT"
    EMBEDDING = "EMBEDDING"


# --- 请求 DTO ---


class CreateModelRequest(BaseModel):
    """创建/更新模型配置请求，与 Java CreateModelRequest 一致。"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    modelName: str = Field(..., min_length=1, description="模型名称（如 qwen2）")
    provider: str = Field(..., min_length=1, description="模型提供商（如 Ollama、OpenAI、DeepSeek）")
    baseUrl: str = Field(..., min_length=1, description="API 基础地址")
    apiKey: Optional[str] = Field(None, description="API 密钥（无密钥则为空）")
    type: ModelType = Field(..., description="模型类型（如 chat、embedding）")
    isEnabled: Optional[bool] = Field(None, description="是否启用：1-启用，0-禁用")
    isDefault: Optional[bool] = Field(None, description="是否默认：1-默认，0-非默认")


class QueryModelRequest(BaseModel):
    """模型查询请求，与 Java QueryModelRequest + PagingQuery 一致。page 从 0 开始，size 默认 20。"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    page: int = Field(0, ge=0, description="页码，从 0 开始")
    size: int = Field(20, gt=0, le=2000, description="每页大小")
    provider: Optional[str] = Field(None, description="模型提供商")
    type: Optional[ModelType] = Field(None, description="模型类型")
    isEnabled: Optional[bool] = Field(None, description="是否启用")
    isDefault: Optional[bool] = Field(None, description="是否默认")


# --- 响应 DTO ---


class ModelsResponse(BaseModel):
    """模型配置响应，与 Java Models 实体字段一致。"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str
    modelName: str
    provider: str
    baseUrl: str
    apiKey: str = ""
    type: str  # "CHAT" | "EMBEDDING"
    isEnabled: bool = True
    isDefault: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    createdBy: Optional[str] = None
    updatedBy: Optional[str] = None


class ProviderItem(BaseModel):
    """厂商项，仅含 provider、baseUrl，与 Java getProviders() 返回结构一致。"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    provider: str
    baseUrl: str
