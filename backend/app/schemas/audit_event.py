import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    id: uuid.UUID
    event_sequence: int

    business_request_id: uuid.UUID | None
    agent_action_id: uuid.UUID | None

    event_type: str
    actor_type: str
    actor_id: str | None

    details: dict[str, Any]

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )