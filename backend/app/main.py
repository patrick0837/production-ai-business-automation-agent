from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import api_router
from .core.config import get_settings
from .db.session import engine
from .infrastructure.redis_client import close_redis_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    await close_redis_client()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(api_router)