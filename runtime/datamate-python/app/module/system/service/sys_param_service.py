"""
System Parameter Service
系统参数服务
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exception import BusinessError, ErrorCodes
from app.db.models.sys_param import SysParam
from app.module.system.schema.sys_param import (
    SysParamDto,
    UpdateParamValueRequest,
    CreateSysParamRequest,
)

logger = get_logger(__name__)


class SysParamService:
    """系统参数服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_params(self) -> List[SysParamDto]:
        """获取系统参数列表"""
        query = select(SysParam).order_by(SysParam.param_type, SysParam.id)
        result = await self.db.execute(query)
        params = result.scalars().all()
        return [self._orm_to_response(p) for p in params]

    async def get_param_by_id(self, param_id: str) -> Optional[SysParamDto]:
        """根据ID获取系统参数"""
        query = select(SysParam).where(SysParam.id == param_id)
        result = await self.db.execute(query)
        param = result.scalar_one_or_none()
        if not param:
            return None
        return self._orm_to_response(param)

    async def update_param_value(self, param_id: str, param_value: str) -> SysParamDto:
        """更新系统参数值"""
        # 查询参数
        query = select(SysParam).where(SysParam.id == param_id)
        result = await self.db.execute(query)
        param = result.scalar_one_or_none()

        if not param:
            raise BusinessError(
                ErrorCodes.NOT_FOUND, f"System parameter {param_id} not found"
            )

        # 检查是否可修改
        if not param.can_modify:
            raise BusinessError(
                ErrorCodes.OPERATION_FAILED,
                f"System parameter {param_id} cannot be modified",
            )

        # 更新值
        param.param_value = param_value
        await self.db.commit()
        await self.db.refresh(param)

        logger.info(f"Updated system parameter {param_id} = {param_value}")
        return self._orm_to_response(param)

    async def create_param(self, request: CreateSysParamRequest) -> SysParamDto:
        """创建系统参数"""
        # 检查是否已存在
        existing = await self.get_param_by_id(request.id)
        if existing:
            raise BusinessError(
                ErrorCodes.OPERATION_FAILED,
                f"System parameter {request.id} already exists",
            )

        # 创建新参数
        param = SysParam(
            id=request.id,
            param_value=request.param_value,
            param_type=request.param_type,
            option_list=request.option_list,
            description=request.description,
            is_built_in=request.is_built_in,
            can_modify=request.can_modify,
            is_enabled=request.is_enabled,
        )

        self.db.add(param)
        await self.db.commit()
        await self.db.refresh(param)

        logger.info(f"Created system parameter {request.id}")
        return self._orm_to_response(param)

    async def delete_param(self, param_id: str) -> None:
        """删除系统参数"""
        # 查询参数
        query = select(SysParam).where(SysParam.id == param_id)
        result = await self.db.execute(query)
        param = result.scalar_one_or_none()

        if not param:
            raise BusinessError(
                ErrorCodes.NOT_FOUND, f"System parameter {param_id} not found"
            )

        # 检查是否为内置参数
        if param.is_built_in:
            raise BusinessError(
                ErrorCodes.OPERATION_FAILED,
                f"Cannot delete built-in system parameter {param_id}",
            )

        # 删除参数
        await self.db.delete(param)
        await self.db.commit()

        logger.info(f"Deleted system parameter {param_id}")

    @staticmethod
    def _orm_to_response(row: SysParam) -> SysParamDto:
        """Convert ORM model to response DTO"""
        return SysParamDto(
            id=row.id,
            param_value=row.param_value,
            param_type=row.param_type or "string",
            option_list=row.option_list,
            description=row.description,
            is_built_in=bool(row.is_built_in) if row.is_built_in is not None else False,
            can_modify=bool(row.can_modify) if row.can_modify is not None else True,
            is_enabled=bool(row.is_enabled) if row.is_enabled is not None else True,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
        )
