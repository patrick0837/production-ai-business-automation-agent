from backend.app.agent import (
    service as agent_service,
)
from backend.app.agent.schemas import (
    AgentModelResponse,
    AgentToolCall,
    ToolExecutionResult,
)
from backend.app.agent.service import (
    AgentService,
)


class FakeProvider:
    def __init__(
            self,
            responses: list[
                AgentModelResponse
            ],
    ):
        self.responses = list(responses)
        self.calls = []

    async def generate_agent_response(
            self,
            messages,
            tools,
    ):
        self.calls.append(
            {
                "messages": [
                    message.copy()
                    for message in messages
                ],
                "tools": tools,
            }
        )

        return self.responses.pop(0)


async def test_agent_completes_without_tool_call():
    provider = FakeProvider(
        responses=[
            AgentModelResponse(
                content=(
                    "No automated action "
                    "is required."
                ),
            )
        ]
    )

    service = AgentService(
        provider=provider,
    )

    result = await service.run(
        source="website",
        content="General information request.",
    )

    assert result.status == "completed"

    assert (
            result.content
            == "No automated action is required."
    )

    assert result.tool_executions == []
    assert len(provider.calls) == 1


async def test_agent_stops_for_human_approval():
    provider = FakeProvider(
        responses=[
            AgentModelResponse(
                tool_calls=[
                    AgentToolCall(
                        id="call-1",
                        name="escalate_incident",
                        arguments={
                            "reason": (
                                "Production payment "
                                "system is down."
                            ),
                            "severity": "urgent",
                        },
                    )
                ]
            )
        ]
    )

    service = AgentService(
        provider=provider,
    )

    result = await service.run(
        source="website",
        content=(
            "Production payment system "
            "is down."
        ),
    )

    assert (
            result.status
            == "approval_required"
    )

    assert len(result.tool_executions) == 1

    execution = result.tool_executions[0]

    assert (
            execution.tool_call.name
            == "escalate_incident"
    )

    assert (
            execution.result.status
            == "approval_required"
    )

    assert len(provider.calls) == 1


async def test_agent_continues_after_completed_tool(
        monkeypatch,
):
    provider = FakeProvider(
        responses=[
            AgentModelResponse(
                tool_calls=[
                    AgentToolCall(
                        name="safe_test_tool",
                        arguments={
                            "value": "test",
                        },
                    )
                ]
            ),
            AgentModelResponse(
                content=(
                    "The requested action "
                    "was completed."
                ),
            ),
        ]
    )

    async def fake_execute_tool(
            name,
            arguments,
            context=None,
    ):
        return ToolExecutionResult(
            tool_name=name,
            status="completed",
            output={
                "result": "success",
            },
        )

    monkeypatch.setattr(
        agent_service,
        "execute_registered_tool_async",
        fake_execute_tool,
    )

    service = AgentService(
        provider=provider,
    )

    result = await service.run(
        source="website",
        content="Run the safe action.",
    )

    assert result.status == "completed"

    assert (
            result.content
            == "The requested action "
               "was completed."
    )

    assert len(result.tool_executions) == 1
    assert len(provider.calls) == 2

    second_call_messages = (
        provider.calls[1]["messages"]
    )

    assert (
            second_call_messages[-2]["role"]
            == "assistant"
    )

    assert (
            second_call_messages[-2]
            ["tool_calls"][0]
            ["function"]["name"]
            == "safe_test_tool"
    )

    assert (
            second_call_messages[-1]["role"]
            == "tool"
    )

    assert (
            second_call_messages[-1]
            ["tool_name"]
            == "safe_test_tool"
    )


async def test_agent_stops_after_max_steps(
        monkeypatch,
):
    provider = FakeProvider(
        responses=[
            AgentModelResponse(
                tool_calls=[
                    AgentToolCall(
                        name="safe_test_tool",
                        arguments={},
                    )
                ]
            ),
            AgentModelResponse(
                tool_calls=[
                    AgentToolCall(
                        name="safe_test_tool",
                        arguments={},
                    )
                ]
            ),
        ]
    )

    async def fake_execute_tool(
            name,
            arguments,
            context=None,
    ):
        return ToolExecutionResult(
            tool_name=name,
            status="completed",
            output={
                "result": "success",
            },
        )

    monkeypatch.setattr(
        agent_service,
        "execute_registered_tool_async",
        fake_execute_tool,
    )

    service = AgentService(
        provider=provider,
        max_steps=2,
    )

    result = await service.run(
        source="website",
        content="Keep calling tools.",
    )

    assert (
            result.status
            == "max_steps_exceeded"
    )

    assert len(provider.calls) == 2

    assert (
            len(result.tool_executions)
            == 2
    )
