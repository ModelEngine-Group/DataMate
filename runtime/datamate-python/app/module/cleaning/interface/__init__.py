from fastapi import APIRouter

from .cleaning_task_routes import router as task_router
from .cleaning_template_routes import router as template_router

router = APIRouter()
router.include_router(task_router)
router.include_router(template_router)
