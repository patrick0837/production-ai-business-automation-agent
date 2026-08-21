from fastapi import APIRouter

from .agent_actions import (
    router as agent_actions_router,
)
from .audit_events import (
    router as audit_events_router,
)
from .requests import (
    router as requests_router,
)


api_v1_router = APIRouter()

api_v1_router.include_router(
    requests_router
)

api_v1_router.include_router(
    agent_actions_router
)

api_v1_router.include_router(
    audit_events_router
)