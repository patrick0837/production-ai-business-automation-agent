from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from ..embeddings.provider import (
    EmbeddingProvider,
)
from .retrieval import (
    KnowledgeSearchResult,
    semantic_search,
)


class DatabaseKnowledgeSearcher:
    def __init__(
            self,
            db: AsyncSession,
            embedding_provider: (
                    EmbeddingProvider | None
            ) = None,
    ) -> None:
        self.db = db
        self.embedding_provider = (
            embedding_provider
        )

    async def __call__(
            self,
            *,
            query: str,
            top_k: int = 5,
            source: str | None = None,
            min_similarity: float | None = None,
    ) -> list[KnowledgeSearchResult]:
        return await semantic_search(
            db=self.db,
            query=query,
            top_k=top_k,
            source=source,
            min_similarity=(
                min_similarity
            ),
            embedding_provider=(
                self.embedding_provider
            ),
        )