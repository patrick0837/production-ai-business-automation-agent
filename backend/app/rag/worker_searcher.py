from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.worker_session import WorkerSessionLocal
from ..embeddings.factory import (
    get_embedding_provider,
)
from ..embeddings.provider import (
    EmbeddingProvider,
)
from ..models.knowledge_chunk import (
    KnowledgeChunk,
)
from ..models.knowledge_document import (
    KnowledgeDocument,
)
from .retrieval import KnowledgeSearchResult


class WorkerKnowledgeSearcher:
    def __init__(
            self,
            embedding_provider: (
                    EmbeddingProvider | None
            ) = None,
            session_factory: (
                    Callable[[], Session] | None
            ) = None,
    ) -> None:
        self.embedding_provider = (
            embedding_provider
        )

        self.session_factory = (
                session_factory
                or WorkerSessionLocal
        )

    async def __call__(
            self,
            *,
            query: str,
            top_k: int = 5,
            source: str | None = None,
            min_similarity: float | None = None,
    ) -> list[KnowledgeSearchResult]:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "Search query must not be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be positive"
            )

        if top_k > 100:
            raise ValueError(
                "top_k must not exceed 100"
            )

        cleaned_source = None

        if source is not None:
            cleaned_source = source.strip()

            if not cleaned_source:
                raise ValueError(
                    "source must not be empty"
                )

        if (
                min_similarity is not None
                and not -1.0
                        <= min_similarity
                        <= 1.0
        ):
            raise ValueError(
                "min_similarity must be "
                "between -1.0 and 1.0"
            )

        provider = (
                self.embedding_provider
                or get_embedding_provider()
        )

        query_embedding = (
            await provider.embed_text(
                cleaned_query
            )
        )

        distance_expression = (
            KnowledgeChunk
            .embedding
            .cosine_distance(
                query_embedding
            )
            .label("distance")
        )

        statement = (
            select(
                KnowledgeChunk,
                KnowledgeDocument,
                distance_expression,
            )
            .join(
                KnowledgeDocument,
                KnowledgeDocument.id
                == KnowledgeChunk.document_id,
                )
            .where(
                KnowledgeChunk.embedding.is_not(
                    None
                )
            )
        )

        if cleaned_source is not None:
            statement = statement.where(
                KnowledgeDocument.source
                == cleaned_source
            )

        if min_similarity is not None:
            maximum_distance = (
                    1.0 - min_similarity
            )

            statement = statement.where(
                distance_expression
                <= maximum_distance
            )

        statement = (
            statement
            .order_by(
                distance_expression.asc(),
                KnowledgeChunk.id.asc(),
            )
            .limit(top_k)
        )

        with self.session_factory() as db:
            result = db.execute(
                statement
            )

            rows = result.all()

            search_results: list[
                KnowledgeSearchResult
            ] = []

            for (
                    chunk,
                    document,
                    distance,
            ) in rows:
                numeric_distance = float(
                    distance
                )

                search_results.append(
                    KnowledgeSearchResult(
                        chunk_id=chunk.id,
                        document_id=(
                            document.id
                        ),
                        document_title=(
                            document.title
                        ),
                        source=(
                            document.source
                        ),
                        chunk_index=(
                            chunk.chunk_index
                        ),
                        content=(
                            chunk.content
                        ),
                        distance=(
                            numeric_distance
                        ),
                        similarity=(
                                1.0
                                - numeric_distance
                        ),
                        document_metadata=(
                            dict(
                                document
                                .document_metadata
                            )
                        ),
                        chunk_metadata=(
                            dict(
                                chunk
                                .chunk_metadata
                            )
                        ),
                    )
                )

        return search_results