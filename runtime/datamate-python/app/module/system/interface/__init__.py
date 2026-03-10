from fastapi import APIRouter

from .about import router as about_router
from app.module.system.interface.models import router as models_router
from .sys_param import router as sys_param_router

router = APIRouter()

router.include_router(about_router)
router.include_router(models_router)
router.include_router(sys_param_router)
