from fastapi import APIRouter

router = APIRouter(
    prefix="/evaluation",
    tags = ["evaluation"]
)

# Include sub-routers
from .evaluation import router as evaluation_router

router.include_router(evaluation_router)
