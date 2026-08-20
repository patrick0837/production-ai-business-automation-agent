import json

import httpx
import pytest

from backend.app.ai.exceptions import (
    InvalidAIResponseError,
    TransientAIProviderError,
)
from backend.app.ai.ollama_provider import OllamaProvider


async def test_ollama_provider_returns_structured_analysis():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        payload = json.loads(request.content)

        assert request.url.path == "/api/chat"
        assert payload["model"] == "qwen3:4b-instruct"
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0

        analysis = {
            "category": "support",
            "priority": "urgent",
            "intent": "service_outage",
            "requires_human_approval": True,
            "recommended_action": (
                "Escalate to incident response."
            ),
        }

        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(analysis),
                },
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler)
    )

    result = await provider.analyze_business_request(
        source="website",
        content="Production system is down.",
    )

    assert result.category == "support"
    assert result.priority == "urgent"
    assert result.intent == "service_outage"
    assert result.requires_human_approval is True


async def test_ollama_provider_marks_503_as_transient():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            503,
            json={
                "error": "Service unavailable",
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
            TransientAIProviderError
    ):
        await provider.analyze_business_request(
            source="website",
            content="Test request",
        )


async def test_ollama_provider_rejects_invalid_response():
    def handler(
            request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": json.dumps(
                        {
                            "category": "support",
                        }
                    ),
                },
            },
        )

    provider = OllamaProvider(
        transport=httpx.MockTransport(handler)
    )

    with pytest.raises(
            InvalidAIResponseError
    ):
        await provider.analyze_business_request(
            source="website",
            content="Test request",
        )