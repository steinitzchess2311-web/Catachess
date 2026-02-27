"""Add deleted_root_id to nodes for recycle bin grouping.

When a folder/study is soft-deleted, all descendants are marked with the same
deleted_root_id pointing to the deletion root. This allows the trash UI to show
only top-level deleted items, and enables atomic restore/purge of entire subtrees.

Revision ID: 20260227_0019
Revises: 20260118_0018
Create Date: 2026-02-27 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260227_0019"
down_revision: Union[str, None] = "20260118_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "nodes",
        sa.Column("deleted_root_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_nodes_deleted_root_id", "nodes", ["deleted_root_id"])


def downgrade() -> None:
    op.drop_index("ix_nodes_deleted_root_id", table_name="nodes")
    op.drop_column("nodes", "deleted_root_id")
