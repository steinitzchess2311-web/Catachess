"""Add chapter tree revision metadata.

Revision ID: 20260709_0020
Revises: 20260227_0019
Create Date: 2026-07-09 00:52:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260709_0020"
down_revision: Union[str, None] = "20260227_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Track saved tree revisions for lightweight collaboration refresh."""
    op.add_column(
        "chapters",
        sa.Column("tree_revision", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "chapters",
        sa.Column("tree_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chapters_tree_revision", "chapters", ["tree_revision"])
    op.alter_column("chapters", "tree_revision", server_default=None)


def downgrade() -> None:
    """Remove chapter tree revision metadata."""
    op.drop_index("ix_chapters_tree_revision", table_name="chapters")
    op.drop_column("chapters", "tree_updated_at")
    op.drop_column("chapters", "tree_revision")
