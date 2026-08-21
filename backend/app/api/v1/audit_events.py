import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...models.audit_event import AuditEvent
from ...schemas.audit_event import AuditEventRead


router = APIRouter(
    prefix="/audit-events",
    tags=["audit-events"],
)


@router.get(
    "",
    response_model=list[AuditEventRead],
)
async def list_audit_events(
        business_request_id: uuid.UUID | None = Query(
            default=None,
        ),
        agent_action_id: uuid.UUID | None = Query(
            default=None,
        ),
        event_type: str | None = Query(
            default=None,
            max_length=100,
        ),
        db: AsyncSession = Depends(get_db),
) -> list[AuditEvent]:
    statement = select(AuditEvent)

    if business_request_id is not None:
        statement = statement.where(
            AuditEvent.business_request_id
            == business_request_id
        )

    if agent_action_id is not None:
        statement = statement.where(
            AuditEvent.agent_action_id
            == agent_action_id
        )

    if event_type is not None:
        statement = statement.where(
            AuditEvent.event_type
            == event_type
        )

    statement = statement.order_by(
        AuditEvent.event_sequence
    )

    result = await db.execute(statement)

    return list(
        result.scalars().all()
    )