"""Add variations and move_annotations tables

Revision ID: 20260110_0002
Revises: 20260110_0001
Create Date: 2026-01-10 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260110_0002'
down_revision: Union[str, None] = '20260110_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create variations and move_annotations tables."""

    # Create variations table
    op.create_table(
        'variations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('chapter_id', sa.String(length=64), nullable=False),
        sa.Column('parent_id', sa.String(length=64), nullable=True),
        sa.Column('next_id', sa.String(length=64), nullable=True),
        sa.Column('move_number', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(length=5), nullable=False),
        sa.Column('san', sa.String(length=20), nullable=False),
        sa.Column('uci', sa.String(length=10), nullable=False),
        sa.Column('fen', sa.String(length=100), nullable=False),
        sa.Column('rank', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='main'),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'),
        sa.Column('pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['variations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['next_id'], ['variations.id'], ondelete='SET NULL'),
    )

    # Create indexes for variations
    op.create_index('ix_variations_chapter_id', 'variations', ['chapter_id'])
    op.create_index('ix_variations_parent_id', 'variations', ['parent_id'])
    op.create_index('ix_variations_chapter_parent_rank', 'variations', ['chapter_id', 'parent_id', 'rank'])

    # Create move_annotations table
    op.create_table(
        'move_annotations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('move_id', sa.String(length=64), nullable=False),
        sa.Column('nag', sa.String(length=10), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('author_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['move_id'], ['variations.id'], ondelete='CASCADE'),
    )

    # Create indexes for move_annotations
    op.create_index('ix_move_annotations_move_id', 'move_annotations', ['move_id'])
    op.create_index('ix_move_annotations_author_id', 'move_annotations', ['author_id'])


def downgrade() -> None:
    """Drop variations and move_annotations tables."""
    op.drop_table('move_annotations')
    op.drop_table('variations')
