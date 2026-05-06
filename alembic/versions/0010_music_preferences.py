"""Add music_preferences to users

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('music_preferences', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'music_preferences')
