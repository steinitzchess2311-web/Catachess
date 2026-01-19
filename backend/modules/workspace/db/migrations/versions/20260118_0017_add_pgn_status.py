"""Add pgn_status to chapters

Revision ID: 20260118_0017
Revises: 20260112_0016
Create Date: 2026-01-18 00:17:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260118_0017"
down_revision: Union[str, None] = "20260112_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgn_status column to chapters."""
    op.add_column("chapters", sa.Column("pgn_status", sa.String(length=32), nullable=True))


def downgrade() -> None:
    """Remove pgn_status column from chapters."""
    op.drop_column("chapters", "pgn_status")
