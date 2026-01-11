"""Add studies and chapters tables

Revision ID: 20260110_0001
Revises: 20260110_0000
Create Date: 2026-01-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260110_0001'
down_revision: Union[str, None] = '20260110_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create studies and chapters tables."""

    # Create studies table
    op.create_table(
        'studies',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('chapter_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id'], ['nodes.id'], ondelete='CASCADE'),
    )

    # Create indexes for studies
    op.create_index('ix_studies_is_public', 'studies', ['is_public'])
    op.create_index('ix_studies_chapter_count', 'studies', ['chapter_count'])

    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('study_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('white', sa.String(length=100), nullable=True),
        sa.Column('black', sa.String(length=100), nullable=True),
        sa.Column('event', sa.String(length=200), nullable=True),
        sa.Column('date', sa.String(length=20), nullable=True),
        sa.Column('result', sa.String(length=10), nullable=True),
        sa.Column('r2_key', sa.String(length=500), nullable=False),
        sa.Column('pgn_hash', sa.String(length=64), nullable=True),
        sa.Column('pgn_size', sa.Integer(), nullable=True),
        sa.Column('r2_etag', sa.String(length=64), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('r2_key', name='uq_chapters_r2_key'),
    )

    # Create indexes for chapters
    op.create_index('ix_chapters_study_id', 'chapters', ['study_id'])
    op.create_index('ix_chapters_study_order', 'chapters', ['study_id', 'order'])
    op.create_index('ix_chapters_r2_key', 'chapters', ['r2_key'])


def downgrade() -> None:
    """Drop studies and chapters tables."""
    op.drop_table('chapters')
    op.drop_table('studies')
