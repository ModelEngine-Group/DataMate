from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router
from .ratio.interface import router as ratio_router
from .generation.interface import router as generation_router
from .evaluation.interface import router as evaluation_router
from .collection.interface import router as collection_route

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)
router.include_router(ratio_router)
router.include_router(generation_router)
router.include_router(evaluation_router)
router.include_router(collection_route)

__all__ = ["router"]
