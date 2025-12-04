from fastapi import APIRouter

router = APIRouter(
    prefix="/synthesis",
    tags = ["synthesis"]
)

# Include sub-routers
from .ratio_task import router as ratio_task_router

router.include_router(ratio_task_router)
