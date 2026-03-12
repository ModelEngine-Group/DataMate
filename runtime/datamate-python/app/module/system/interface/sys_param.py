"""
System Parameter API Routes
系统参数 REST API 路由
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.module.shared.schema.common import StandardResponse
from app.module.system.schema.sys_param import (
    SysParamDto,
    UpdateParamValueRequest,
    CreateSysParamRequest,
)
from app.module.system.service.sys_param_service import SysParamService

router = APIRouter(prefix="/sys-param", tags=["System Parameters"])


@router.get(
    "/list",
    response_model=StandardResponse[List[SysParamDto]],
    summary="获取系统参数列表",
    description="获取所有系统参数配置",
)
async def list_params(db: AsyncSession = Depends(get_db)):
    """获取系统参数列表"""
    service = SysParamService(db)
    params = await service.list_params()
    return StandardResponse(code="0", message="success", data=params)


@router.get(
    "/{param_id}",
    response_model=StandardResponse[SysParamDto],
    summary="获取系统参数详情",
    description="根据ID获取系统参数详情",
)
async def get_param(
    param_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取系统参数详情"""
    service = SysParamService(db)
    param = await service.get_param_by_id(param_id)
    if not param:
        from app.core.exception import BusinessError, ErrorCodes

        raise BusinessError(
            ErrorCodes.NOT_FOUND, f"System parameter {param_id} not found"
        )
    return StandardResponse(code="0", message="success", data=param)


@router.post(
    "",
    response_model=StandardResponse[SysParamDto],
    summary="创建系统参数",
    description="创建新的系统参数",
)
async def create_param(
    request: CreateSysParamRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建系统参数"""
    service = SysParamService(db)
    param = await service.create_param(request)
    await db.commit()
    return StandardResponse(code="0", message="success", data=param)


@router.put(
    "/{param_id}",
    response_model=StandardResponse[SysParamDto],
    summary="更新系统参数值",
    description="更新指定系统参数的值",
)
async def update_param_value(
    param_id: str,
    request: UpdateParamValueRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新系统参数值"""
    service = SysParamService(db)
    param = await service.update_param_value(param_id, request.param_value)
    await db.commit()
    return StandardResponse(code="0", message="success", data=param)


@router.delete(
    "/{param_id}",
    response_model=StandardResponse[str],
    summary="删除系统参数",
    description="删除指定的系统参数",
)
async def delete_param(
    param_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除系统参数"""
    service = SysParamService(db)
    await service.delete_param(param_id)
    await db.commit()
    return StandardResponse(code="0", message="success", data=param_id)
