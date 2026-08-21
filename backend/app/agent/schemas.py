from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolExecutionResult(BaseModel):
    tool_name: str

    status: Literal[
        "completed",
        "approval_required",
    ]

    output: dict[str, Any] = Field(
        default_factory=dict,
    )