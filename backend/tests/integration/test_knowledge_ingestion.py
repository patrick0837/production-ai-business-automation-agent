from sqlalchemy import select

from backend.app.models.knowledge_chunk import (
    KnowledgeChunk,
)
from backend.app.models.knowledge_document import (
    KnowledgeDocument,
)
from backend.app.rag.ingestion import (
    ingest_knowledge_document,
)


class FakeEmbeddingProvider:
    async def embed_text(
            self,
            text: str,
    ) -> list[float]:
        return [0.1] * 768

    async def embed_batch(
            self,
            texts: list[str],
    ) -> list[list[float]]:
        return [
            [float(index + 1)] * 768
            for index, _ in enumerate(texts)
        ]


async def test_ingest_knowledge_document(
        db_session,
):
    content = " ".join(
        f"policy{i}"
        for i in range(12)
    )

    document = await ingest_knowledge_document(
        db=db_session,
        title="Refund Policy",
        source="internal-policy",
        content=content,
        document_metadata={
            "department": "support",
        },
        embedding_provider=(
            FakeEmbeddingProvider()
        ),
        chunk_size_words=5,
        overlap_words=2,
    )

    assert document.id is not None
    assert document.title == "Refund Policy"

    assert (
            document.document_metadata[
                "department"
            ]
            == "support"
    )

    document_result = await db_session.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id
            == document.id
        )
    )

    stored_document = (
        document_result.scalar_one()
    )

    assert (
            stored_document.source
            == "internal-policy"
    )

    chunk_result = await db_session.execute(
        select(KnowledgeChunk)
        .where(
            KnowledgeChunk.document_id
            == document.id
        )
        .order_by(
            KnowledgeChunk.chunk_index
        )
    )

    chunks = list(
        chunk_result.scalars().all()
    )

    assert len(chunks) == 4

    assert [
               chunk.chunk_index
               for chunk in chunks
           ] == [
               0,
               1,
               2,
               3,
           ]

    assert (
            chunks[0].content
            == "policy0 policy1 policy2 "
               "policy3 policy4"
    )

    assert (
            chunks[1].content
            == "policy3 policy4 policy5 "
               "policy6 policy7"
    )

    assert (
            len(chunks[0].embedding)
            == 768
    )

    assert (
            chunks[0].embedding_model
            == "nomic-embed-text:v1.5"
    )