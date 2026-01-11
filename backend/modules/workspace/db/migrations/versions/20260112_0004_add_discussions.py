"""Add discussions table

Revision ID: 20260112_0004
Revises: 20260111_0003
Create Date: 2026-01-12 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260112_0004"
down_revision: Union[str, None] = "20260111_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discussions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("author_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("thread_type", sa.String(length=20), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discussions_target_id", "discussions", ["target_id"])
    op.create_index("ix_discussions_target_type", "discussions", ["target_type"])


def downgrade() -> None:
    op.drop_index("ix_discussions_target_type", table_name="discussions")
    op.drop_index("ix_discussions_target_id", table_name="discussions")
    op.drop_table("discussions")
