"""
Tables for System Settings Management

Derived from scripts/db/setting-management-init.sql
 - t_model_config
 - t_sys_param
"""

import uuid
from sqlalchemy import Column, String, Text, TIMESTAMP, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, Text as TextType

from app.db.session import Base


class ModelConfig(Base):
    """Model Configuration Table (UUID primary key) -> t_model_config

    Stores configuration for different AI models used in the system.
    """
    __tablename__ = "t_model_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="Primary Key ID")
    model_name = Column(String(100), nullable=False, comment="Model name (e.g., qwen2)")
    provider = Column(String(50), nullable=False, comment="Model provider (e.g., Ollama, OpenAI, DeepSeek)")
    base_url = Column(String(255), nullable=False, comment="API base URL")
    api_key = Column(String(512), default="", comment="API key (empty if no key required)")
    type = Column(String(50), nullable=False, comment="Model type (e.g., chat, embedding)")
    is_enabled = Column(Boolean, default=True, comment="Whether enabled: 1-enabled, 0-disabled")
    is_default = Column(Boolean, default=False, comment="Whether default: 1-default, 0-non-default")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="Creation time")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Update time"
    )
    created_by = Column(String(255), nullable=True, comment="Creator")
    updated_by = Column(String(255), nullable=True, comment="Updater")

    def __repr__(self) -> str:
        return f"<ModelConfig(id={self.id}, model={self.provider}/{self.model_name}, type={self.type})>"


class SystemParameter(Base):
    """System Parameter Table (UUID primary key) -> t_sys_param

    Stores system configuration parameters with various types and constraints.
    """
    __tablename__ = "t_sys_param"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="Primary Key ID")
    param_key = Column(String(100), nullable=False, unique=True, comment="Parameter key")
    param_value = Column(Text, nullable=False, comment="Parameter value")
    param_type = Column(String(50), default="string", comment="Parameter type (string, number, boolean, enum)")
    option_list = Column(Text, nullable=True, comment="Comma-separated options (for enum type)")
    description = Column(String(255), default="", comment="Parameter description")
    is_built_in = Column(Boolean, default=False, comment="Whether built-in: 1-yes, 0-no")
    can_modify = Column(Boolean, default=True, comment="Whether modifiable: 1-yes, 0-no")
    is_enabled = Column(Boolean, default=True, comment="Whether enabled: 1-enabled, 0-disabled")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="Creation time")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="Update time"
    )
    created_by = Column(String(255), nullable=True, comment="Creator")
    updated_by = Column(String(255), nullable=True, comment="Updater")

    def __repr__(self) -> str:
        return f"<SystemParameter(key={self.param_key}, type={self.param_type}, value={self.param_value[:20]}...)>"
