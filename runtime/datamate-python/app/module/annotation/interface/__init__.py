from fastapi import APIRouter

from .about import router as about_router
from .project import router as project_router
from .task import router as task_router
from .template import router as template_router

router = APIRouter(
    prefix="/annotation",
    tags = ["annotation"]
)

router.include_router(about_router)
router.include_router(project_router)
router.include_router(task_router)
router.include_router(template_router)