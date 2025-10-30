from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)

__all__ = ["router"]