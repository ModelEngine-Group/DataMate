from fastapi import APIRouter

from .system.interface import router as system_router
from .annotation.interface import router as annotation_router
from .ratio.interface import router as ratio_router
from .generation.interface import router as generation_router
from .evaluation.interface import router as evaluation_router
from .collection.interface import router as collection_route
from .operator.interface import operator_router
from .operator.interface import category_router
from .cleaning.interface import router as cleaning_router
from .rag.interface.knowledge_base import router as knowledge_base_router

router = APIRouter(
    prefix="/api"
)

router.include_router(system_router)
router.include_router(annotation_router)
router.include_router(ratio_router)
router.include_router(generation_router)
router.include_router(evaluation_router)
router.include_router(collection_route)
router.include_router(operator_router)
router.include_router(category_router)
router.include_router(cleaning_router)
router.include_router(knowledge_base_router)

__all__ = ["router"]
