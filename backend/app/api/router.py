from fastapi import APIRouter

from .health import router as health_router
from .v1.router import api_v1_router

api_router = APIRouter()

api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    api_v1_router,
    prefix="/api/v1",
)