"""通用系统服务：仅保留与 DB 直接相关的查询。LLM 创建与调用统一使用 app.core.llm.LLMFactory。"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.models import Models


async def get_model_by_id(db: AsyncSession, model_id: str) -> Optional[Models]:
    """根据模型ID获取未删除的 Models 记录。"""
    q = select(Models).where(Models.id == model_id).where(
        (Models.is_deleted == False) | (Models.is_deleted.is_(None))
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()
