"""add verification codes table

Revision ID: 002
Revises: 001
Create Date: 2026-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verification_codes table
    op.create_table(
        'verification_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.String(length=50), nullable=False, server_default='signup'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_verification_codes_user_id', 'verification_codes', ['user_id'])
    op.create_index('idx_verification_active', 'verification_codes', ['user_id', 'purpose', 'consumed_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_verification_active', table_name='verification_codes')
    op.drop_index('ix_verification_codes_user_id', table_name='verification_codes')

    # Drop table
    op.drop_table('verification_codes')
