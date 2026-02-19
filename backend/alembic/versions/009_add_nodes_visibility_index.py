"""Add composite index on nodes (visibility, node_type)

Revision ID: 009_add_nodes_visibility_index
Revises: 008_create_blog_images_table
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '009_add_nodes_visibility_index'
down_revision = '008_create_blog_images_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_nodes_visibility_type',
        'nodes',
        ['visibility', 'node_type'],
    )


def downgrade():
    op.drop_index('ix_nodes_visibility_type', table_name='nodes')
