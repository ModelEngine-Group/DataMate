"""
模型配置 REST 接口：与 Java ModelConfigController 路径、语义一致，响应使用 StandardResponse。
db 通过 ModelConfigService 的 Depends(get_db) 注入，不在本层传递。
"""
from fastapi import APIRouter, Depends, Query

from app.module.shared.schema import StandardResponse, PaginatedData
from app.module.system.schema import (
    CreateModelRequest,
    QueryModelRequest,
    ModelConfigResponse,
    ProviderItem,
    ModelType,
)
from app.module.system.service.model_config_service import ModelConfigService

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/providers", response_model=StandardResponse[list[ProviderItem]])
async def get_providers(svc: ModelConfigService = Depends()):
    """获取厂商列表，与 Java GET /models/providers 一致。"""
    data = await svc.get_providers()
    return StandardResponse(code=200, message="success", data=data)


@router.get("/list", response_model=StandardResponse[PaginatedData[ModelConfigResponse]])
async def get_models(
    page: int = Query(0, ge=0, description="页码，从 0 开始"),
    size: int = Query(20, gt=0, le=500, description="每页大小"),
    provider: str | None = Query(None, description="模型提供商"),
    type: ModelType | None = Query(None, description="模型类型"),
    isEnabled: bool | None = Query(None, description="是否启用"),
    isDefault: bool | None = Query(None, description="是否默认"),
    svc: ModelConfigService = Depends(),
):
    """分页查询模型列表，与 Java GET /models/list 一致。"""
    q = QueryModelRequest(
        page=page,
        size=size,
        provider=provider,
        type=type,
        isEnabled=isEnabled,
        isDefault=isDefault,
    )
    data = await svc.get_models(q)
    return StandardResponse(code=200, message="success", data=data)


@router.post("/create", response_model=StandardResponse[ModelConfigResponse])
async def create_model(req: CreateModelRequest, svc: ModelConfigService = Depends()):
    """创建模型配置，与 Java POST /models/create 一致。"""
    data = await svc.create_model(req)
    return StandardResponse(code=200, message="success", data=data)


@router.get("/{model_id}", response_model=StandardResponse[ModelConfigResponse])
async def get_model_detail(model_id: str, svc: ModelConfigService = Depends()):
    """获取模型详情，与 Java GET /models/{modelId} 一致。"""
    data = await svc.get_model_detail(model_id)
    return StandardResponse(code=200, message="success", data=data)


@router.put("/{model_id}", response_model=StandardResponse[ModelConfigResponse])
async def update_model(
    model_id: str,
    req: CreateModelRequest,
    svc: ModelConfigService = Depends(),
):
    """更新模型配置，与 Java PUT /models/{modelId} 一致。"""
    data = await svc.update_model(model_id, req)
    return StandardResponse(code=200, message="success", data=data)


@router.delete("/{model_id}", response_model=StandardResponse[None])
async def delete_model(model_id: str, svc: ModelConfigService = Depends()):
    """删除模型配置，与 Java DELETE /models/{modelId} 一致。"""
    await svc.delete_model(model_id)
    return StandardResponse(code=200, message="success", data=None)
