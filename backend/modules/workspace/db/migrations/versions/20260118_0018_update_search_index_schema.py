"""Update search_index schema with author_id and search_vector.

Revision ID: 20260118_0018
Revises: 20260118_0017
Create Date: 2026-01-18 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260118_0018"
down_revision: Union[str, None] = "20260118_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("search_index", sa.Column("author_id", sa.String(length=64), nullable=True))
    op.add_column(
        "search_index",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            nullable=True,
        ),
    )
    op.create_index("ix_search_index_author", "search_index", ["author_id"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "UPDATE search_index SET search_vector = to_tsvector('english', content)"
        )


def downgrade() -> None:
    op.drop_index("ix_search_index_author", table_name="search_index")
    op.drop_column("search_index", "search_vector")
    op.drop_column("search_index", "author_id")
