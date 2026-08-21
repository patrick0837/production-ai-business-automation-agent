"""add RAG knowledge tables

Revision ID: ee50891cacba
Revises: 40bcfbea731b
Create Date: 2026-08-21 22:28:24.866161
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ee50891cacba"
down_revision: Union[str, Sequence[str], None] = (
    "40bcfbea731b"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create RAG knowledge document and chunk tables."""

    op.create_table(
        "knowledge_documents",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_knowledge_documents"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_knowledge_documents_created_at"
        ),
        "knowledge_documents",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_knowledge_documents_source"
        ),
        "knowledge_documents",
        ["source"],
        unique=False,
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            VECTOR(dim=768),
            nullable=True,
        ),
        sa.Column(
            "embedding_model",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            name=op.f(
                "fk_knowledge_chunks_"
                "document_id_knowledge_documents"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_knowledge_chunks"
            ),
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name=(
                "uq_knowledge_chunks_"
                "document_chunk_index"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_knowledge_chunks_created_at"
        ),
        "knowledge_chunks",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_knowledge_chunks_document_id"
        ),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove RAG knowledge tables."""

    op.drop_index(
        op.f(
            "ix_knowledge_chunks_document_id"
        ),
        table_name="knowledge_chunks",
    )

    op.drop_index(
        op.f(
            "ix_knowledge_chunks_created_at"
        ),
        table_name="knowledge_chunks",
    )

    op.drop_table(
        "knowledge_chunks"
    )

    op.drop_index(
        op.f(
            "ix_knowledge_documents_source"
        ),
        table_name="knowledge_documents",
    )

    op.drop_index(
        op.f(
            "ix_knowledge_documents_created_at"
        ),
        table_name="knowledge_documents",
    )

    op.drop_table(
        "knowledge_documents"
    )