from typing import Any, Protocol

from ..agent.schemas import AgentModelResponse
from ..schemas.ai_analysis import BusinessRequestAnalysis


class AIProvider(Protocol):
    async def analyze_business_request(
            self,
            source: str,
            content: str,
    ) -> BusinessRequestAnalysis:
        ...

    async def generate_agent_response(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]],
    ) -> AgentModelResponse:
        ...