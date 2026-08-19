import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BusinessRequestCreate(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class BusinessRequestRead(BaseModel):
    id: uuid.UUID
    source: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)