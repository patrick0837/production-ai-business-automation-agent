import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from .api.router import api_router
from .core.config import get_settings
from .core.logging_config import (
    configure_logging,
)
from .db.session import engine
from .infrastructure.redis_client import (
    close_redis_client,
)

settings = get_settings()

configure_logging(settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Application started",
        extra={
            "event": "application_started",
        },
    )

    yield

    logger.info(
        "Application shutting down",
        extra={
            "event": "application_shutdown",
        },
    )

    await close_redis_client()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(
        request: Request,
        call_next,
):
    request_id = (
            request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
    )

    request.state.request_id = request_id

    started_at = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        duration_ms = round(
            (
                    time.perf_counter()
                    - started_at
            )
            * 1000,
            2,
            )

        logger.exception(
            "HTTP request failed",
            extra={
                "event": "http_request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )

        raise

    duration_ms = round(
        (
                time.perf_counter()
                - started_at
        )
        * 1000,
        2,
        )

    response.headers[
        "X-Request-ID"
    ] = request_id

    logger.info(
        "HTTP request completed",
        extra={
            "event": "http_request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": (
                response.status_code
            ),
            "duration_ms": duration_ms,
        },
    )

    return response


app.include_router(api_router)