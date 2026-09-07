from collections.abc import (
    Awaitable,
    Callable,
)
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from .context import AgentExecutionContext
from .schemas import ToolExecutionResult
from .tools import (
    EscalateIncidentInput,
    RequestReimbursementInput,
    SearchKnowledgeBaseInput,
    escalate_incident,
    request_reimbursement,
    search_knowledge_base,
)


SyncToolHandler = Callable[
    [Any],
    ToolExecutionResult,
]

AsyncToolHandler = Callable[
    [
        Any,
        AgentExecutionContext,
    ],
    Awaitable[ToolExecutionResult],
]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    input_model: type[BaseModel]

    handler: (
            SyncToolHandler | None
    ) = None

    async_handler: (
            AsyncToolHandler | None
    ) = None

    requires_approval: bool = False

    requires_knowledge_search: (
        bool
    ) = False

    def to_ollama_spec(
            self,
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    self.description
                ),
                "parameters": (
                    self.input_model
                    .model_json_schema()
                ),
            },
        }

    def is_available(
            self,
            context: (
                    AgentExecutionContext | None
            ),
    ) -> bool:
        if (
                self.requires_knowledge_search
        ):
            return (
                    context is not None
                    and context
                    .knowledge_searcher
                    is not None
            )

        return True


TOOL_REGISTRY: dict[
    str,
    RegisteredTool,
] = {
    "escalate_incident": RegisteredTool(
        name="escalate_incident",
        description=(
            "Escalate a critical incident to the human "
            "operations team. Use this tool when the "
            "request or retrieved company policy requires "
            "an incident to be escalated. This is a "
            "high-impact action and requires human approval."
        ),
        input_model=(
            EscalateIncidentInput
        ),
        handler=escalate_incident,
        requires_approval=True,
    ),

    "request_reimbursement": RegisteredTool(
        name="request_reimbursement",
        description=(
            "Request an actual reimbursement, refund, "
            "or other financial reimbursement action. "
            "Use this tool when the user asks for money "
            "to be reimbursed or refunded, or asks the "
            "system to perform a reimbursement action. "
            "Do not use this tool for informational "
            "questions about reimbursement or refund "
            "policy; use search_knowledge_base instead. "
            "This is a financial action and always "
            "requires human approval."
        ),
        input_model=(
            RequestReimbursementInput
        ),
        handler=request_reimbursement,
        requires_approval=True,
    ),

    "search_knowledge_base": (
        RegisteredTool(
            name="search_knowledge_base",
            description=(
                "Search the internal company "
                "knowledge base for policies, "
                "procedures, support guidance, "
                "and other business-specific "
                "information."
            ),
            input_model=(
                SearchKnowledgeBaseInput
            ),
            async_handler=(
                search_knowledge_base
            ),
            requires_knowledge_search=True,
        )
    ),
}


def get_tool_specs(
        context: (
                AgentExecutionContext | None
        ) = None,
) -> list[dict[str, Any]]:
    return [
        tool.to_ollama_spec()
        for tool in TOOL_REGISTRY.values()
        if tool.is_available(context)
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
                    validated_arguments
                    .model_dump()
                ),
            },
        )

    if tool.handler is None:
        raise RuntimeError(
            f"Tool {name} requires "
            "asynchronous execution"
        )

    return tool.handler(
        validated_arguments
    )


async def execute_registered_tool_async(
        name: str,
        arguments: dict[str, Any],
        context: (
                AgentExecutionContext | None
        ) = None,
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
                    validated_arguments
                    .model_dump()
                ),
            },
        )

    if tool.async_handler is not None:
        if context is None:
            raise RuntimeError(
                f"Tool {name} requires "
                "an agent execution context"
            )

        return await tool.async_handler(
            validated_arguments,
            context,
        )

    if tool.handler is None:
        raise RuntimeError(
            f"Tool {name} has no handler"
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

    if tool.handler is None:
        raise RuntimeError(
            f"Approved tool {name} does "
            "not support synchronous "
            "execution"
        )

    return tool.handler(
        validated_arguments
    )