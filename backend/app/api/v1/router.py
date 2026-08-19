from fastapi import APIRouter

from .requests import router as requests_router

api_v1_router = APIRouter()

api_v1_router.include_router(requests_router)