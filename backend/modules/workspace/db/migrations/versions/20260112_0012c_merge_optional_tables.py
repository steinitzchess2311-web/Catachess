"""Merge optional tables revisions

Revision ID: 20260112_0012c
Revises: 20260112_0012a, 20260112_0012b
Create Date: 2026-01-12 16:30:00.000000
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401

revision: str = "20260112_0012c"
down_revision: Union[str, Sequence[str], None] = ("20260112_0012a", "20260112_0012b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
