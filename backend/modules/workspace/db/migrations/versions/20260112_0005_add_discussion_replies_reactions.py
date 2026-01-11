"""Add discussion replies and reactions tables

Revision ID: 20260112_0005
Revises: 20260112_0004
Create Date: 2026-01-12 10:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260112_0005"
down_revision: Union[str, None] = "20260112_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discussion_replies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("thread_id", sa.String(length=64), nullable=False),
        sa.Column("parent_reply_id", sa.String(length=64), nullable=True),
        sa.Column("quote_reply_id", sa.String(length=64), nullable=True),
        sa.Column("author_id", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("edited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("edit_history", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["thread_id"], ["discussions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_reply_id"], ["discussion_replies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_reply_id"], ["discussion_replies.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_discussion_replies_thread_id", "discussion_replies", ["thread_id"])
    op.create_index("ix_discussion_replies_parent_id", "discussion_replies", ["parent_reply_id"])

    op.create_table(
        "discussion_reactions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=16), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("emoji", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discussion_reactions_target", "discussion_reactions", ["target_id", "target_type"])
    op.create_index("ix_discussion_reactions_user", "discussion_reactions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_discussion_reactions_user", table_name="discussion_reactions")
    op.drop_index("ix_discussion_reactions_target", table_name="discussion_reactions")
    op.drop_table("discussion_reactions")
    op.drop_index("ix_discussion_replies_parent_id", table_name="discussion_replies")
    op.drop_index("ix_discussion_replies_thread_id", table_name="discussion_replies")
    op.drop_table("discussion_replies")
