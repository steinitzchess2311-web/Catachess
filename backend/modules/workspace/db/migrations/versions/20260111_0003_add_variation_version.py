"""Add version field to variations for optimistic locking.

Revision ID: 20260111_0003
Revises: 20260110_0002
Create Date: 2026-01-11 00:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260111_0003"
down_revision: Union[str, None] = "20260110_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add version column to variations table."""
    op.add_column(
        "variations",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    """Remove version column from variations table."""
    op.drop_column("variations", "version")
