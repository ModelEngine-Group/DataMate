from fastapi import APIRouter

router = APIRouter(
    prefix="/data-collection",
    tags = ["data-collection"]
)

# Include sub-routers
from .collection import router as collection_router
from .execution import router as execution_router
from .template import router as template_router

router.include_router(collection_router)
router.include_router(execution_router)
router.include_router(template_router)
