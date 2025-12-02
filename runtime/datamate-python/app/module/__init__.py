from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router
from .synthesis.interface import router as ratio_router
from .generation.interface import router as generation_router

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)
router.include_router(ratio_router)
router.include_router(generation_router)

__all__ = ["router"]
