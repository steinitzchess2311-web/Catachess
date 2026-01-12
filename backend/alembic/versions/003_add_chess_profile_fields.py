"""add chess profile fields to users

Revision ID: 003
Revises: 002
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add chess profile fields to users table
    # All fields are nullable (optional) as users will set them in settings after signup

    # Online chess platform usernames
    op.add_column('users', sa.Column('lichess_username', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('chesscom_username', sa.String(length=50), nullable=True))

    # Chess ratings from different organizations
    op.add_column('users', sa.Column('fide_rating', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('cfc_rating', sa.Integer(), nullable=True))  # Chess Federation of Canada
    op.add_column('users', sa.Column('ecf_rating', sa.Integer(), nullable=True))  # English Chess Federation

    # Chess titles
    op.add_column('users', sa.Column('chinese_athlete_title', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('fide_title', sa.String(length=10), nullable=True))  # GM, IM, FM, CM, WGM, WIM, WFM, WCM

    # Self introduction
    op.add_column('users', sa.Column('self_intro', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove chess profile fields
    op.drop_column('users', 'self_intro')
    op.drop_column('users', 'fide_title')
    op.drop_column('users', 'chinese_athlete_title')
    op.drop_column('users', 'ecf_rating')
    op.drop_column('users', 'cfc_rating')
    op.drop_column('users', 'fide_rating')
    op.drop_column('users', 'chesscom_username')
    op.drop_column('users', 'lichess_username')
