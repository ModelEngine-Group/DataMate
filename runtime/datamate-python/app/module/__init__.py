from fastapi import APIRouter

from .annotation.interface import router as annotation_router

router = APIRouter(
    prefix="/api"
)

router.include_router(annotation_router)

__all__ = ["router"]