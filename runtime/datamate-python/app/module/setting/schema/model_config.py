"""
Schema definitions for model configuration in system settings.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ModelConfigBase(BaseModel):
    """Base model for model configuration"""
    model_name: str = Field(..., max_length=100, description="Model name (e.g., qwen2)")
    provider: str = Field(..., max_length=50, description="Model provider (e.g., Ollama, OpenAI, DeepSeek)")
    base_url: str = Field(..., max_length=255, description="API base URL")
    api_key: str = Field(default="", max_length=512, description="API key (empty if no key required)")
    type: str = Field(..., max_length=50, description="Model type (e.g., chat, embedding)")
    is_enabled: bool = Field(default=True, description="Whether the model is enabled")
    is_default: bool = Field(default=False, description="Whether this is the default model")


class ModelConfigInDBBase(ModelConfigBase):
    """Base model for model configuration in database"""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class ModelConfigInDB(ModelConfigInDBBase):
    """Model configuration in database"""
    pass
