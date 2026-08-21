from typing import Any

import httpx

from ..agent.schemas import (
    AgentModelResponse,
    AgentToolCall,
)
from ..core.config import get_settings
from ..schemas.ai_analysis import BusinessRequestAnalysis
from .exceptions import (
    AIProviderError,
    InvalidAIResponseError,
    TransientAIProviderError,
)


TRANSIENT_HTTP_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


class OllamaProvider:
    def __init__(
            self,
            transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()

        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.transport = transport

    async def _post_chat(
            self,
            payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                    base_url=self.base_url,
                    timeout=120.0,
                    transport=self.transport,
            ) as client:
                response = await client.post(
                    "/api/chat",
                    json=payload,
                )

            if (
                    response.status_code
                    in TRANSIENT_HTTP_STATUS_CODES
            ):
                raise TransientAIProviderError(
                    "Ollama is temporarily unavailable "
                    f"(HTTP {response.status_code})"
                )

            response.raise_for_status()

        except (
                httpx.TimeoutException,
                httpx.NetworkError,
        ) as exc:
            raise TransientAIProviderError(
                "Unable to reach Ollama"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                "Ollama request failed with "
                f"HTTP {exc.response.status_code}"
            ) from exc

        try:
            response_body = response.json()

            if not isinstance(response_body, dict):
                raise TypeError

            return response_body

        except (
                TypeError,
                ValueError,
        ) as exc:
            raise InvalidAIResponseError(
                "Ollama returned invalid JSON"
            ) from exc

    async def analyze_business_request(
            self,
            source: str,
            content: str,
    ) -> BusinessRequestAnalysis:
        system_prompt = """
You classify incoming business requests.

Priority rules:
- urgent: immediate service outage, security incident, major business blocker,
  or explicitly time-critical request
- high: important enterprise request requiring prompt attention
- normal: standard business request
- low: informational or non-urgent request

Human approval should be true when the recommended action could create
significant business, financial, security, legal, or customer-facing impact.

Return only data matching the provided JSON schema.
""".strip()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        f"Source: {source}\n"
                        f"Request: {content}"
                    ),
                },
            ],
            "format": (
                BusinessRequestAnalysis.model_json_schema()
            ),
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        response_body = await self._post_chat(
            payload
        )

        try:
            message = response_body["message"]
            content_json = message["content"]

            if not isinstance(content_json, str):
                raise TypeError

            return (
                BusinessRequestAnalysis
                .model_validate_json(content_json)
            )

        except (
                KeyError,
                TypeError,
                ValueError,
        ) as exc:
            raise InvalidAIResponseError(
                "Ollama returned an invalid "
                "business request analysis"
            ) from exc

    async def generate_agent_response(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]],
    ) -> AgentModelResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        response_body = await self._post_chat(
            payload
        )

        try:
            message = response_body["message"]

            if not isinstance(message, dict):
                raise TypeError

            content = message.get("content") or ""

            if not isinstance(content, str):
                raise TypeError

            raw_tool_calls = (
                    message.get("tool_calls") or []
            )

            if not isinstance(raw_tool_calls, list):
                raise TypeError

            tool_calls: list[AgentToolCall] = []

            for raw_tool_call in raw_tool_calls:
                if not isinstance(
                        raw_tool_call,
                        dict,
                ):
                    raise TypeError

                function = raw_tool_call["function"]

                if not isinstance(function, dict):
                    raise TypeError

                name = function["name"]
                arguments = function.get(
                    "arguments",
                    {},
                )

                if (
                        not isinstance(name, str)
                        or not name
                ):
                    raise TypeError

                if not isinstance(arguments, dict):
                    raise TypeError

                tool_calls.append(
                    AgentToolCall(
                        id=raw_tool_call.get("id"),
                        name=name,
                        arguments=arguments,
                    )
                )

            return AgentModelResponse(
                content=content,
                tool_calls=tool_calls,
            )

        except (
                KeyError,
                TypeError,
                ValueError,
        ) as exc:
            raise InvalidAIResponseError(
                "Ollama returned an invalid "
                "agent response"
            ) from exc