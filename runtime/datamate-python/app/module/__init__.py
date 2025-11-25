from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router
from .synthesis.interface import router as ratio_router

#新增：引入 QA 模块路由
from .generation.interface.qa_generation import router as qa_generation_router

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)
router.include_router(ratio_router)

#新增：挂载 QA 模块
router.include_router(qa_generation_router, prefix="/generation")

__all__ = ["router"]
