from typing import Literal

from pydantic import BaseModel, Field


class BusinessRequestAnalysis(BaseModel):
    category: Literal[
        "sales",
        "support",
        "billing",
        "technical",
        "other",
    ]

    priority: Literal[
        "low",
        "normal",
        "high",
        "urgent",
    ]

    intent: str = Field(
        min_length=1,
        max_length=200,
    )

    requires_human_approval: bool

    recommended_action: str = Field(
        min_length=1,
        max_length=500,
    )