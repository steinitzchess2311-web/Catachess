"""Add presence_sessions table

Revision ID: 20260112_0011
Revises: 20260112_0010
Create Date: 2026-01-12 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260112_0011"
down_revision: Union[str, None] = "20260112_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "presence_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("study_id", sa.String(length=64), nullable=False),
        sa.Column("chapter_id", sa.String(length=64), nullable=True),
        sa.Column("move_path", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_presence_sessions_study_id", "presence_sessions", ["study_id"])
    op.create_index("ix_presence_sessions_user_id", "presence_sessions", ["user_id"])
    op.create_index("ix_presence_sessions_last_heartbeat", "presence_sessions", ["last_heartbeat"])
    # Unique constraint: one active session per user per study
    op.create_index("ix_presence_sessions_user_study", "presence_sessions", ["user_id", "study_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_presence_sessions_user_study", table_name="presence_sessions")
    op.drop_index("ix_presence_sessions_last_heartbeat", table_name="presence_sessions")
    op.drop_index("ix_presence_sessions_user_id", table_name="presence_sessions")
    op.drop_index("ix_presence_sessions_study_id", table_name="presence_sessions")
    op.drop_table("presence_sessions")
