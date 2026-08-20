from fastapi import APIRouter, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..core.config import get_settings
from ..db.session import engine
from ..infrastructure.redis_client import redis_client

router = APIRouter()


@router.get("/health")
def health_check():
    settings = get_settings()

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness_check():
    database_ok = False
    redis_ok = False

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            database_ok = result.scalar_one() == 1
    except SQLAlchemyError:
        database_ok = False

    try:
        redis_ok = bool(await redis_client.ping())
    except RedisError:
        redis_ok = False

    if not database_ok or not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "dependencies": {
                    "database": database_ok,
                    "redis": redis_ok,
                },
            },
        )

    return {
        "status": "ready",
        "dependencies": {
            "database": True,
            "redis": True,
        },
    }