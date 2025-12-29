from fastapi import APIRouter

router = APIRouter(
    prefix="/data-collection",
    tags = ["data-collection"]
)

# Include sub-routers
from .collection import router as collection_router

router.include_router(collection_router)
