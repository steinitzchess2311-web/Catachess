"""Add idempotency_cache table

Revision ID: 20260112_0012
Revises: 20260112_0011
Create Date: 2026-01-12 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260112_0012"
down_revision: Union[str, None] = "20260112_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_cache",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index("ix_idempotency_cache_expires_at", "idempotency_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_cache_expires_at", table_name="idempotency_cache")
    op.drop_table("idempotency_cache")
