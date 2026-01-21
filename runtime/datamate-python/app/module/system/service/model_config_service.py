"""
模型配置应用服务：与 Java ModelConfigApplicationService 行为一致。
包含分页、详情、增改删、isDefault 互斥逻辑及健康检查。
"""
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.model_config import ModelConfig
from app.module.system.schema.model_config import (
    ModelType,
    CreateModelRequest,
    QueryModelRequest,
    ModelConfigResponse,
    ProviderItem,
)
from app.module.shared.schema import PaginatedData
from app.module.system.service.common_service import get_chat_client, get_openai_client

logger = get_logger(__name__)

# 固定厂商列表，与 Java getProviders() 一致
PROVIDERS = [
    ProviderItem(provider="ModelEngine", baseUrl="http://localhost:9981"),
    ProviderItem(provider="Ollama", baseUrl="http://localhost:11434"),
    ProviderItem(provider="OpenAI", baseUrl="https://api.openai.com/v1"),
    ProviderItem(provider="DeepSeek", baseUrl="https://api.deepseek.com/v1"),
    ProviderItem(provider="火山方舟", baseUrl="https://ark.cn-beijing.volces.com/api/v3"),
    ProviderItem(provider="阿里云百炼", baseUrl="https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ProviderItem(provider="硅基流动", baseUrl="https://api.siliconflow.cn/v1"),
    ProviderItem(provider="智谱AI", baseUrl="https://open.bigmodel.cn/api/paas/v4"),
]


def _check_model_health(model_name: str, base_url: str, api_key: Optional[str], model_type: ModelType) -> None:
    """对配置做一次最小化模型调用进行健康检查，失败则抛出 MODEL_HEALTH_CHECK_FAILED。"""
    # 构造满足 common_service 接口的只读对象
    class _ModelLike:
        def __init__(self, name: str, url: str, key: str, t: str):
            self.model_name = name
            self.base_url = url
            self.api_key = key or ""
            self.type = t

    m = _ModelLike(model_name, base_url, api_key or "", model_type.value)
    try:
        if model_type == ModelType.CHAT:
            chat = get_chat_client(m)  # type: ignore[arg-type]
            chat.invoke("hello")
        else:
            emb = get_openai_client(m)  # type: ignore[arg-type]
            emb.embed_query("text")
    except Exception as e:
        logger.error("Model health check failed: model=%s type=%s err=%s", model_name, model_type, e)
        raise HTTPException(status_code=400, detail="模型健康检查失败") from e


def _orm_to_response(row: ModelConfig) -> ModelConfigResponse:
    return ModelConfigResponse(
        id=row.id,
        modelName=row.model_name,
        provider=row.provider,
        baseUrl=row.base_url,
        apiKey=row.api_key or "",
        type=row.type or "CHAT",
        isEnabled=bool(row.is_enabled) if row.is_enabled is not None else True,
        isDefault=bool(row.is_default) if row.is_default is not None else False,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
        createdBy=row.created_by,
        updatedBy=row.updated_by,
    )


async def get_providers() -> list[ProviderItem]:
    """返回固定厂商列表，与 Java getProviders() 一致。"""
    return list(PROVIDERS)


async def get_models(db: AsyncSession, q: QueryModelRequest) -> PaginatedData[ModelConfigResponse]:
    """分页查询，支持 provider/type/isEnabled/isDefault；page 从 0 开始，与 Java 一致。"""
    query = select(ModelConfig)
    if q.provider is not None and q.provider != "":
        query = query.where(ModelConfig.provider == q.provider)
    if q.type is not None:
        query = query.where(ModelConfig.type == q.type.value)
    if q.isEnabled is not None:
        query = query.where(ModelConfig.is_enabled == (1 if q.isEnabled else 0))
    if q.isDefault is not None:
        query = query.where(ModelConfig.is_default == (1 if q.isDefault else 0))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    size = max(1, min(500, q.size))
    offset = max(0, q.page) * size
    rows = (
        await db.execute(
            query.order_by(ModelConfig.created_at.desc()).offset(offset).limit(size)
        )
    ).scalars().all()
    total_pages = math.ceil(total / size) if total else 0
    # 响应中 page 使用 1-based，与 PaginatedData 注释一致
    current = max(0, q.page) + 1
    return PaginatedData(
        page=current,
        size=size,
        total_elements=total,
        total_pages=total_pages,
        content=[_orm_to_response(r) for r in rows],
    )


async def get_model_detail(db: AsyncSession, model_id: str) -> ModelConfigResponse:
    """获取模型详情，不存在则 404。"""
    r = (await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return _orm_to_response(r)


async def create_model(db: AsyncSession, req: CreateModelRequest) -> ModelConfigResponse:
    """创建模型：健康检查后 saveAndSetDefault；isEnabled 恒为 True。"""
    _check_model_health(req.modelName, req.baseUrl, req.apiKey, req.type)

    # 同类型下是否已有默认
    existing = (
        await db.execute(
            select(ModelConfig).where(
                ModelConfig.type == req.type.value,
                ModelConfig.is_default == 1,
            )
        )
    ).scalar_one_or_none()

    is_default: bool
    if existing is None:
        is_default = True
    else:
        # 清除同类型默认
        await db.execute(
            update(ModelConfig)
            .where(ModelConfig.type == req.type.value, ModelConfig.is_default == 1)
            .values(is_default=0)
        )
        is_default = req.isDefault if req.isDefault is not None else False

    now = datetime.now(timezone.utc)
    entity = ModelConfig(
        id=str(uuid.uuid4()),
        model_name=req.modelName,
        provider=req.provider,
        base_url=req.baseUrl,
        api_key=req.apiKey or "",
        type=req.type.value,
        is_enabled=1,
        is_default=1 if is_default else 0,
        created_at=now,
        updated_at=now,
        created_by=None,
        updated_by=None,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return _orm_to_response(entity)


async def update_model(db: AsyncSession, model_id: str, req: CreateModelRequest) -> ModelConfigResponse:
    """更新模型：存在性校验、健康检查后 updateAndSetDefault；isEnabled 恒为 True。"""
    entity = (await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="模型配置不存在")

    entity.model_name = req.modelName
    entity.provider = req.provider
    entity.base_url = req.baseUrl
    entity.api_key = req.apiKey or ""
    entity.type = req.type.value
    entity.is_enabled = 1

    _check_model_health(req.modelName, req.baseUrl, req.apiKey, req.type)

    want_default = req.isDefault if req.isDefault is not None else False
    if (entity.is_default != 1) and want_default:
        await db.execute(
            update(ModelConfig)
            .where(ModelConfig.type == req.type.value, ModelConfig.is_default == 1)
            .values(is_default=0)
        )
    entity.is_default = 1 if want_default else 0
    entity.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(entity)
    return _orm_to_response(entity)


async def delete_model(db: AsyncSession, model_id: str) -> None:
    """删除模型配置。"""
    entity = (await db.execute(select(ModelConfig).where(ModelConfig.id == model_id))).scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    await db.delete(entity)
    await db.commit()
