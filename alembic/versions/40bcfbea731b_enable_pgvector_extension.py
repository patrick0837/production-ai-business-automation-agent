"""enable pgvector extension

Revision ID: 40bcfbea731b
Revises: 39ebf9acec4b
Create Date: 2026-08-21 22:23:46.962828
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "40bcfbea731b"
down_revision: Union[str, Sequence[str], None] = (
    "39ebf9acec4b"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable the pgvector PostgreSQL extension."""
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )


def downgrade() -> None:
    """Disable the pgvector PostgreSQL extension."""
    op.execute(
        "DROP EXTENSION IF EXISTS vector"
    )