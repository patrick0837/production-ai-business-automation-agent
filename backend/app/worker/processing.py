import asyncio

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