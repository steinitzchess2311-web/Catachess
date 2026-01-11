"""Initial workspace schema

Revision ID: 20260110_0000
Revises:
Create Date: 2026-01-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260110_0000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all workspace tables."""

    # Create nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('node_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('owner_id', sa.String(length=64), nullable=False),
        sa.Column('visibility', sa.String(length=20), nullable=False),
        sa.Column('parent_id', sa.String(length=64), nullable=True),
        sa.Column('path', sa.String(length=1000), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['nodes.id'], ondelete='CASCADE'),
    )

    # Create indexes for nodes
    op.create_index('ix_nodes_owner_id', 'nodes', ['owner_id'])
    op.create_index('ix_nodes_parent_id', 'nodes', ['parent_id'])
    op.create_index('ix_nodes_path', 'nodes', ['path'])
    op.create_index('ix_nodes_node_type', 'nodes', ['node_type'])
    op.create_index('ix_nodes_deleted_at', 'nodes', ['deleted_at'])

    # Create ACL table
    op.create_table(
        'acl',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('object_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('inherit_to_children', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_inherited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('inherited_from', sa.String(length=64), nullable=True),
        sa.Column('granted_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['object_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('object_id', 'user_id', name='uq_acl_object_user'),
    )

    # Create indexes for ACL
    op.create_index('ix_acl_object_id', 'acl', ['object_id'])
    op.create_index('ix_acl_user_id', 'acl', ['user_id'])
    op.create_index('ix_acl_permission', 'acl', ['permission'])

    # Create share_links table
    op.create_table(
        'share_links',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('object_id', sa.String(length=64), nullable=False),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('permission', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['object_id'], ['nodes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('token', name='uq_share_links_token'),
    )

    # Create indexes for share_links
    op.create_index('ix_share_links_object_id', 'share_links', ['object_id'])
    op.create_index('ix_share_links_token', 'share_links', ['token'])

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('aggregate_type', sa.String(length=50), nullable=False),
        sa.Column('aggregate_id', sa.String(length=64), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for events
    op.create_index('ix_events_aggregate_type', 'events', ['aggregate_type'])
    op.create_index('ix_events_aggregate_id', 'events', ['aggregate_id'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])
    op.create_index('ix_events_actor_id', 'events', ['actor_id'])
    op.create_index('ix_events_timestamp', 'events', ['timestamp'])
    op.create_index('ix_events_aggregate_version', 'events', ['aggregate_id', 'version'], unique=True)


def downgrade() -> None:
    """Drop all workspace tables."""
    op.drop_table('events')
    op.drop_table('share_links')
    op.drop_table('acl')
    op.drop_table('nodes')
