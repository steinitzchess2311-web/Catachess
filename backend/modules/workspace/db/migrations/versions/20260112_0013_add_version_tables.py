"""Add version history tables

Revision ID: 20260112_0013
Revises: 20260112_0012c
Create Date: 2026-01-12 01:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260112_0013'
down_revision = '20260112_0012c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create study_versions table
    op.create_table(
        'study_versions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('study_id', sa.String(64), nullable=False, index=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('snapshot_key', sa.String(512), nullable=True),
        sa.Column('is_rollback', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create unique constraint on study_id + version_number
    op.create_unique_constraint(
        'uq_study_versions_study_version',
        'study_versions',
        ['study_id', 'version_number']
    )

    # Create index on created_at for time-based queries
    op.create_index(
        'ix_study_versions_created_at',
        'study_versions',
        ['created_at']
    )

    # Create version_snapshots table (metadata only, content in R2)
    op.create_table(
        'version_snapshots',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('version_id', sa.String(64), nullable=False, index=True),
        sa.Column('r2_key', sa.String(512), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create foreign key to study_versions
    op.create_foreign_key(
        'fk_version_snapshots_version_id',
        'version_snapshots',
        'study_versions',
        ['version_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_table('version_snapshots')
    op.drop_table('study_versions')
