from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel

from .schemas import ToolExecutionResult
from .tools import (
    EscalateIncidentInput,
    escalate_incident,
)


ToolHandler = Callable[
    [Any],
    ToolExecutionResult,
]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: ToolHandler
    requires_approval: bool = False

    def to_ollama_spec(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": (
                    self.input_model.model_json_schema()
                ),
            },
        }


TOOL_REGISTRY: dict[str, RegisteredTool] = {
    "escalate_incident": RegisteredTool(
        name="escalate_incident",
        description=(
            "Escalate a critical production incident "
            "to the human operations team."
        ),
        input_model=EscalateIncidentInput,
        handler=escalate_incident,
        requires_approval=True,
    ),
}


def get_tool_specs() -> list[dict[str, Any]]:
    return [
        tool.to_ollama_spec()
        for tool in TOOL_REGISTRY.values()
    ]


def _get_validated_tool(
        name: str,
        arguments: dict[str, Any],
) -> tuple[
    RegisteredTool,
    BaseModel,
]:
    try:
        tool = TOOL_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown agent tool: {name}"
        ) from exc

    validated_arguments = (
        tool.input_model.model_validate(
            arguments
        )
    )

    return tool, validated_arguments


def execute_registered_tool(
        name: str,
        arguments: dict[str, Any],
) -> ToolExecutionResult:
    tool, validated_arguments = (
        _get_validated_tool(
            name=name,
            arguments=arguments,
        )
    )

    if tool.requires_approval:
        return ToolExecutionResult(
            tool_name=name,
            status="approval_required",
            output={
                "arguments": (
                    validated_arguments.model_dump()
                ),
            },
        )

    return tool.handler(
        validated_arguments
    )


def execute_approved_tool(
        name: str,
        arguments: dict[str, Any],
) -> ToolExecutionResult:
    tool, validated_arguments = (
        _get_validated_tool(
            name=name,
            arguments=arguments,
        )
    )

    return tool.handler(
        validated_arguments
    )