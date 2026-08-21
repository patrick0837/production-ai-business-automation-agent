import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    business_request_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        Uuid,
        ForeignKey(
            "business_requests.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    agent_action_id: Mapped[
        uuid.UUID | None
        ] = mapped_column(
        Uuid,
        ForeignKey(
            "agent_actions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    actor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    actor_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    details: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )