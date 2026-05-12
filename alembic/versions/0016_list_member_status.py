"""add status column to list_members for invite flow

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'list_members',
        sa.Column('status', sa.String(20), nullable=False, server_default='accepted'),
    )


def downgrade():
    op.drop_column('list_members', 'status')
