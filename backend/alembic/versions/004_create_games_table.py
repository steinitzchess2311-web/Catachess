"""create games table

Revision ID: 004
Revises: 003
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create games table
    # Stores game metadata. PGN data is stored in R2.
    op.create_table(
        'games',
        sa.Column('game_id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),

        # Game metadata (from PGN tags)
        sa.Column('player_white', sa.String(length=100), nullable=True),
        sa.Column('player_black', sa.String(length=100), nullable=True),
        sa.Column('event', sa.String(length=200), nullable=True),
        sa.Column('site', sa.String(length=100), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('result', sa.String(length=10), nullable=False, server_default='*'),

        # Game progress tracking
        sa.Column('move_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_fen', sa.String(length=100), nullable=True),

        # R2 storage reference
        sa.Column('r2_key', sa.String(length=500), nullable=False, unique=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create index on user_id for faster queries
    op.create_index('ix_games_user_id', 'games', ['user_id'])


def downgrade() -> None:
    # Drop games table
    op.drop_index('ix_games_user_id', table_name='games')
    op.drop_table('games')
