from fastapi import APIRouter

from .project import router as project_router
from .task import router as task_router

router = APIRouter(
    prefix="/annotation",
    tags = ["annotation"]
)

router.include_router(project_router)
router.include_router(task_router)