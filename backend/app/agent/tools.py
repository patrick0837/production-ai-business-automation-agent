from typing import Literal

from pydantic import BaseModel, Field

from .schemas import ToolExecutionResult


class EscalateIncidentInput(BaseModel):
    reason: str = Field(
        min_length=1,
        max_length=1000,
    )

    severity: Literal[
        "high",
        "urgent",
    ]


def escalate_incident(
        arguments: EscalateIncidentInput,
) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name="escalate_incident",
        status="completed",
        output={
            "severity": arguments.severity,
            "reason": arguments.reason,
            "message": (
                "Incident escalation has been prepared "
                "for the human operations team."
            ),
        },
    )