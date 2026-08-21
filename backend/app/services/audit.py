import uuid
from typing import Any

from ..models.audit_event import AuditEvent


def create_audit_event(
        *,
        event_type: str,
        actor_type: str,
        business_request_id: uuid.UUID | None = None,
        agent_action_id: uuid.UUID | None = None,
        actor_id: str | None = None,
        details: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        business_request_id=business_request_id,
        agent_action_id=agent_action_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        details=details or {},
    )