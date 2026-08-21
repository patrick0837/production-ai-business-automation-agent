import asyncio

from ..agent.schemas import AgentRunResult
from ..agent.service import AgentService
from ..ai.exceptions import TransientAIProviderError
from ..ai.factory import get_ai_provider
from ..schemas.ai_analysis import BusinessRequestAnalysis
from .exceptions import TransientProcessingError


def analyze_business_request(
        source: str,
        content: str,
) -> BusinessRequestAnalysis:
    provider = get_ai_provider()

    try:
        return asyncio.run(
            provider.analyze_business_request(
                source=source,
                content=content,
            )
        )

    except TransientAIProviderError as exc:
        raise TransientProcessingError(
            "AI provider is temporarily unavailable"
        ) from exc


def run_agent(
        source: str,
        content: str,
) -> AgentRunResult:
    service = AgentService()

    try:
        return asyncio.run(
            service.run(
                source=source,
                content=content,
            )
        )

    except TransientAIProviderError as exc:
        raise TransientProcessingError(
            "AI agent provider is temporarily unavailable"
        ) from exc