from backend.app.models.knowledge_chunk import (
    KnowledgeChunk,
)
from backend.app.models.knowledge_document import (
    KnowledgeDocument,
)
from backend.app.rag.retrieval import (
    semantic_search,
)


EMBEDDING_DIMENSIONS = 768


def make_vector(
        index: int,
        value: float = 1.0,
) -> list[float]:
    vector = [
        0.0
        for _ in range(
            EMBEDDING_DIMENSIONS
        )
    ]

    vector[index] = value

    return vector


class FakeEmbeddingProvider:
    def __init__(
            self,
            vector: list[float],
    ):
        self.vector = vector

    async def embed_text(
            self,
            text: str,
    ) -> list[float]:
        return self.vector

    async def embed_batch(
            self,
            texts: list[str],
    ) -> list[list[float]]:
        return [
            self.vector
            for _ in texts
        ]


async def create_test_knowledge(
        db_session,
):
    support_document = KnowledgeDocument(
        title="Support Policy",
        source="support",
        document_metadata={
            "department": "support",
        },
    )

    hr_document = KnowledgeDocument(
        title="HR Policy",
        source="hr",
        document_metadata={
            "department": "hr",
        },
    )

    db_session.add_all(
        [
            support_document,
            hr_document,
        ]
    )

    await db_session.flush()

    chunks = [
        KnowledgeChunk(
            document_id=(
                support_document.id
            ),
            chunk_index=0,
            content=(
                "Security incidents must "
                "be escalated immediately."
            ),
            embedding=make_vector(0),
            embedding_model="test-model",
            chunk_metadata={},
        ),
        KnowledgeChunk(
            document_id=(
                support_document.id
            ),
            chunk_index=1,
            content=(
                "Refund requests are "
                "reviewed by support."
            ),
            embedding=make_vector(1),
            embedding_model="test-model",
            chunk_metadata={},
        ),
        KnowledgeChunk(
            document_id=hr_document.id,
            chunk_index=0,
            content=(
                "Employees should contact "
                "HR about annual leave."
            ),
            embedding=make_vector(
                0,
                -1.0,
            ),
            embedding_model="test-model",
            chunk_metadata={},
        ),
    ]

    db_session.add_all(chunks)

    await db_session.flush()


async def test_semantic_search_orders_by_similarity(
        db_session,
):
    await create_test_knowledge(
        db_session
    )

    results = await semantic_search(
        db=db_session,
        query="security incident",
        embedding_provider=(
            FakeEmbeddingProvider(
                make_vector(0)
            )
        ),
    )

    assert len(results) == 3

    assert (
            results[0].content
            == "Security incidents must "
               "be escalated immediately."
    )

    assert results[0].similarity == 1.0

    assert (
            results[1].content
            == "Refund requests are "
               "reviewed by support."
    )

    assert results[1].similarity == 0.0

    assert (
            results[2].content
            == "Employees should contact "
               "HR about annual leave."
    )

    assert results[2].similarity == -1.0


async def test_semantic_search_respects_top_k(
        db_session,
):
    await create_test_knowledge(
        db_session
    )

    results = await semantic_search(
        db=db_session,
        query="security incident",
        top_k=1,
        embedding_provider=(
            FakeEmbeddingProvider(
                make_vector(0)
            )
        ),
    )

    assert len(results) == 1

    assert (
            results[0].document_title
            == "Support Policy"
    )


async def test_semantic_search_filters_by_source(
        db_session,
):
    await create_test_knowledge(
        db_session
    )

    results = await semantic_search(
        db=db_session,
        query="company policy",
        source="hr",
        embedding_provider=(
            FakeEmbeddingProvider(
                make_vector(0)
            )
        ),
    )

    assert len(results) == 1
    assert results[0].source == "hr"
    assert (
            results[0].document_title
            == "HR Policy"
    )


async def test_semantic_search_filters_by_similarity(
        db_session,
):
    await create_test_knowledge(
        db_session
    )

    results = await semantic_search(
        db=db_session,
        query="security incident",
        min_similarity=0.5,
        embedding_provider=(
            FakeEmbeddingProvider(
                make_vector(0)
            )
        ),
    )

    assert len(results) == 1

    assert (
            results[0].content
            == "Security incidents must "
               "be escalated immediately."
    )