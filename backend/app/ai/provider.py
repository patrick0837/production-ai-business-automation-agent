from typing import Protocol

from ..schemas.ai_analysis import BusinessRequestAnalysis


class AIProvider(Protocol):
    async def analyze_business_request(
            self,
            source: str,
            content: str,
    ) -> BusinessRequestAnalysis:
        ...