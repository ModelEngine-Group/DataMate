from fastapi import APIRouter

router = APIRouter(
    prefix="/synth",
    tags = ["synth"]
)

# Include sub-routers
from .generation_api import router as generation_router_router

router.include_router(generation_router_router)
