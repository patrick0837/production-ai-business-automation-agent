from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentToolCall(BaseModel):
    id: str | None = None

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )


class AgentModelResponse(BaseModel):
    content: str = ""

    tool_calls: list[AgentToolCall] = Field(
        default_factory=list,
    )


class ToolExecutionResult(BaseModel):
    tool_name: str

    status: Literal[
        "completed",
        "approval_required",
    ]

    output: dict[str, Any] = Field(
        default_factory=dict,
    )