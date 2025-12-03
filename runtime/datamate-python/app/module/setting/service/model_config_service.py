"""
Service layer for managing model configurations in system settings.
"""
from typing import Optional

from sqlalchemy import select, update, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.setting_management import ModelConfig
from app.module.setting.schema.model_config import (
    ModelConfigInDB,
)

logger = get_logger(__name__)


class ModelConfigService:
    def __init__(self, db: AsyncSession):
        """
        初始化 DM 客户端

        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("Initialize ModelConfig service client (Database mode)")

    async def get_model_config(self, config_id: str) -> Optional[ModelConfigInDB]:
        """
        Get a model configuration by ID

        Args:
            db: Database session
            config_id: ID of the model configuration

        Returns:
            The model configuration if found, None otherwise
        """
        result = await self.db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
        config = result.scalar_one_or_none()

        return ModelConfigInDB(
            id=config.id,
            model_name=config.model_name,
            base_url=config.base_url,
            api_key=config.api_key,
            provider=config.provider,
            type=config.type,
            is_enabled=config.is_enabled,
            is_default=config.is_default,
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by=config.created_by,
            updated_by=config.updated_by
        ) if config else None
