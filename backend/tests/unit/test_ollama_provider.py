import httpx
import pytest

from backend.app.ai.exceptions import (
    InvalidAIResponseError,
    TransientAIProviderError,
)
from backend.app.ai.ollama_provider import (
    OllamaProvider,
)


@pytest.mark.asyncio
async def test_ollama_provider_returns_valid_analysis():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": (
                        "{"
                        '"category":"support",'
                        '"priority":"urgent",'
                        '"intent":"service_outage",'
                        '"requires_human_approval":true,'
                        '"recommended_action":'
                        '"Escalate immediately."'
                        "}"
                    )
                }
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    result = (
        await provider.analyze_business_request(
            source="website",
            content="Production system is down.",
        )
    )

    assert result.category == "support"
    assert result.priority == "urgent"
    assert result.intent == "service_outage"
    assert result.requires_human_approval is True
    assert (
            result.recommended_action
            == "Escalate immediately."
    )


@pytest.mark.asyncio
async def test_ollama_provider_treats_503_as_transient():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "error": "temporarily unavailable",
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
            TransientAIProviderError
    ):
        await provider.analyze_business_request(
            source="website",
            content="Test request",
        )


@pytest.mark.asyncio
async def test_ollama_provider_rejects_invalid_analysis():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": (
                        '{"category":"support"}'
                    )
                }
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
            InvalidAIResponseError
    ):
        await provider.analyze_business_request(
            source="website",
            content="Test request",
        )


@pytest.mark.asyncio
async def test_agent_response_normalizes_tool_calls():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-123",
                            "function": {
                                "index": 0,
                                "name": (
                                    "escalate_incident"
                                ),
                                "arguments": {
                                    "reason": (
                                        "Production outage"
                                    ),
                                    "severity": "urgent",
                                },
                            },
                        }
                    ],
                }
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    result = await provider.generate_agent_response(
        messages=[
            {
                "role": "user",
                "content": "Production is down.",
            }
        ],
        tools=[],
    )

    assert result.content == ""
    assert len(result.tool_calls) == 1

    tool_call = result.tool_calls[0]

    assert tool_call.id == "call-123"
    assert (
            tool_call.name
            == "escalate_incident"
    )
    assert (
            tool_call.arguments["severity"]
            == "urgent"
    )


@pytest.mark.asyncio
async def test_agent_response_can_return_text_only():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": (
                        "No automated action is required."
                    )
                }
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    result = await provider.generate_agent_response(
        messages=[
            {
                "role": "user",
                "content": "General information request.",
            }
        ],
        tools=[],
    )

    assert (
            result.content
            == "No automated action is required."
    )
    assert result.tool_calls == []


@pytest.mark.asyncio
async def test_agent_response_rejects_invalid_tool_arguments():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": (
                                    "escalate_incident"
                                ),
                                "arguments": (
                                    "not-an-object"
                                ),
                            }
                        }
                    ],
                }
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(
            InvalidAIResponseError
    ):
        await provider.generate_agent_response(
            messages=[
                {
                    "role": "user",
                    "content": "Production is down.",
                }
            ],
            tools=[],
        )