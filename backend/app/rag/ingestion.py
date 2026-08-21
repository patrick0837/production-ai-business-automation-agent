from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
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
from .chunking import chunk_text


async def ingest_knowledge_document(
        *,
        db: AsyncSession,
        title: str,
        source: str,
        content: str,
        document_metadata: (
                dict[str, Any] | None
        ) = None,
        embedding_provider: (
                EmbeddingProvider | None
        ) = None,
        chunk_size_words: int = 180,
        overlap_words: int = 30,
) -> KnowledgeDocument:
    cleaned_title = title.strip()
    cleaned_source = source.strip()

    if not cleaned_title:
        raise ValueError(
            "Knowledge document title "
            "must not be empty"
        )

    if not cleaned_source:
        raise ValueError(
            "Knowledge document source "
            "must not be empty"
        )

    chunks = chunk_text(
        content,
        chunk_size_words=chunk_size_words,
        overlap_words=overlap_words,
    )

    provider = (
            embedding_provider
            or get_embedding_provider()
    )

    embeddings = await provider.embed_batch(
        chunks
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match "
            "knowledge chunk count"
        )

    settings = get_settings()

    document = KnowledgeDocument(
        title=cleaned_title,
        source=cleaned_source,
        document_metadata=(
                document_metadata or {}
        ),
    )

    db.add(document)

    await db.flush()

    for index, (
            chunk_content,
            embedding,
    ) in enumerate(
        zip(
            chunks,
            embeddings,
            strict=True,
        )
    ):
        knowledge_chunk = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk_content,
            embedding=embedding,
            embedding_model=(
                settings
                .ollama_embedding_model
            ),
            chunk_metadata={},
        )

        db.add(knowledge_chunk)

    await db.commit()
    await db.refresh(document)

    return document