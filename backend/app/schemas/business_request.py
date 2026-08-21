import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BusinessRequestCreate(BaseModel):
    source: str = Field(
        min_length=1,
        max_length=100,
    )
    content: str = Field(
        min_length=1,
    )


class BusinessRequestRead(BaseModel):
    id: uuid.UUID
    source: str
    content: str
    status: str
    celery_task_id: str | None = None

    category: str | None = None
    priority: str | None = None
    intent: str | None = None
    requires_human_approval: bool | None = None
    recommended_action: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )