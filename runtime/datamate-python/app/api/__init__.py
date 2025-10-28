"""
API 路由模块

集中管理所有API路由的组织结构
"""
from fastapi import APIRouter

from .system import router as system_router
from .project import project_router

# 创建主API路由器
api_router = APIRouter()

# 注册到主路由器
api_router.include_router(system_router, tags=["系统"])
api_router.include_router(project_router, prefix="/project", tags=["项目"])

# 导出路由器供 main.py 使用
__all__ = ["api_router"]