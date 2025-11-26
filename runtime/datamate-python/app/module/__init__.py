from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router
from .synthesis.interface import router as ratio_router

# QA生成模块路由 (已合并到 synthesis 模块)
from .synthesis.interface.qa_generation import router as qa_generation_router

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)
router.include_router(ratio_router)

# 挂载 QA 生成模块 (在 synthesis 命名空间下)
router.include_router(qa_generation_router, prefix="/synthesis")

__all__ = ["router"]
