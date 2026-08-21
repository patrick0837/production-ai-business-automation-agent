import uuid
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class AgentActionRead(BaseModel):
    id: uuid.UUID
    business_request_id: uuid.UUID

    tool_call_id: str | None = None
    tool_name: str

    arguments: dict[str, Any]

    status: str
    requires_approval: bool

    result: dict[str, Any] | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AgentActionReject(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=1000,
    )