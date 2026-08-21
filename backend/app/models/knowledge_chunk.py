import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


EMBEDDING_DIMENSIONS = 768


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name=(
                "uq_knowledge_chunks_"
                "document_chunk_index"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "knowledge_documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[
        list[float] | None
        ] = mapped_column(
        VECTOR(EMBEDDING_DIMENSIONS),
        nullable=True,
    )

    embedding_model: Mapped[
        str | None
        ] = mapped_column(
        String(150),
        nullable=True,
    )

    chunk_metadata: Mapped[
        dict[str, Any]
    ] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )