from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Protocol

from ..rag.retrieval import (
    KnowledgeSearchResult,
)


class KnowledgeSearcher(Protocol):
    def __call__(
            self,
            *,
            query: str,
            top_k: int = 5,
            source: str | None = None,
            min_similarity: float | None = None,
    ) -> Awaitable[
        list[KnowledgeSearchResult]
    ]:
        ...


@dataclass(
    frozen=True,
    slots=True,
)
class AgentExecutionContext:
    knowledge_searcher: (
            KnowledgeSearcher | None
    ) = None