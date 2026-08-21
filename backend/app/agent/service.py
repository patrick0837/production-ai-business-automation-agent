import json
from typing import Any

from ..ai.factory import get_ai_provider
from ..ai.provider import AIProvider
from .registry import (
    execute_registered_tool,
    get_tool_specs,
)
from .schemas import (
    AgentModelResponse,
    AgentRunResult,
    AgentToolExecution,
)


SYSTEM_PROMPT = """
You are a business automation agent.

Your job is to understand business requests and use the
available tools when an action is required.

Rules:
- Use tools when they are appropriate.
- Never claim that an action was completed unless a tool
  result confirms it.
- Do not invent tool results.
- High-impact actions may require human approval.
- After receiving a tool result, decide whether another
  tool is required or return a final response.
""".strip()


class AgentService:
    def __init__(
            self,
            provider: AIProvider | None = None,
            max_steps: int = 5,
    ) -> None:
        if max_steps < 1:
            raise ValueError(
                "max_steps must be at least 1"
            )

        self.provider = (
            provider
            if provider is not None
            else get_ai_provider()
        )

        self.max_steps = max_steps

    async def run(
            self,
            source: str,
            content: str,
    ) -> AgentRunResult:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Source: {source}\n"
                    f"Request: {content}"
                ),
            },
        ]

        tools = get_tool_specs()

        executions: list[
            AgentToolExecution
        ] = []

        last_content = ""

        for _ in range(self.max_steps):
            response = (
                await self.provider
                .generate_agent_response(
                    messages=messages,
                    tools=tools,
                )
            )

            last_content = response.content

            if not response.tool_calls:
                return AgentRunResult(
                    status="completed",
                    content=response.content,
                    tool_executions=executions,
                )

            messages.append(
                self._build_assistant_message(
                    response
                )
            )

            for tool_call in response.tool_calls:
                result = execute_registered_tool(
                    name=tool_call.name,
                    arguments=tool_call.arguments,
                )

                execution = AgentToolExecution(
                    tool_call=tool_call,
                    result=result,
                )

                executions.append(execution)

                if (
                        result.status
                        == "approval_required"
                ):
                    return AgentRunResult(
                        status="approval_required",
                        content=response.content,
                        tool_executions=executions,
                    )

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": (
                            tool_call.name
                        ),
                        "content": json.dumps(
                            result.output,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        return AgentRunResult(
            status="max_steps_exceeded",
            content=last_content,
            tool_executions=executions,
        )

    @staticmethod
    def _build_assistant_message(
            response: AgentModelResponse,
    ) -> dict[str, Any]:
        tool_calls = []

        for index, tool_call in enumerate(
                response.tool_calls
        ):
            tool_calls.append(
                {
                    "type": "function",
                    "function": {
                        "index": index,
                        "name": tool_call.name,
                        "arguments": (
                            tool_call.arguments
                        ),
                    },
                }
            )

        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": tool_calls,
        }