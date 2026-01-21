from fastapi import APIRouter

from .about import router as about_router
from .model_config import router as model_config_router

router = APIRouter()

router.include_router(about_router)
router.include_router(model_config_router)