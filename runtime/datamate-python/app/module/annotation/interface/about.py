from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.module.shared.schema import StandardResponse
from app.module.dataset import DatasetManagementService
from app.core.logging import get_logger
from app.core.config import settings
from app.exception import NoDatasetInfoFoundError, DatasetMappingNotFoundError

from ..client import LabelStudioClient
from ..service.sync import SyncService
from ..service.mapping import DatasetMappingService
from ..schema import (
    ConfigResponse
)


router = APIRouter(
    prefix="/about",
    tags=["annotation/about"]
)
logger = get_logger(__name__)

@router.get("", response_model=StandardResponse[ConfigResponse])
async def get_config():
    """获取配置信息"""
    return StandardResponse(
        code=200,
        message="success",
        data=ConfigResponse(
            label_studio_url=settings.label_studio_base_url,
        )
    )