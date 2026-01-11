"""Add search index table

Revision ID: 20260112_0006
Revises: 20260112_0005
Create Date: 2026-01-12 10:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260112_0006"
down_revision: Union[str, None] = "20260112_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_index",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_search_index_target", "search_index", ["target_id", "target_type"])


def downgrade() -> None:
    op.drop_index("ix_search_index_target", table_name="search_index")
    op.drop_table("search_index")
