from fastapi import APIRouter

from .about import router as about_router
from app.module.system.interface.models import router as models_router

router = APIRouter()

router.include_router(about_router)
router.include_router(models_router)
