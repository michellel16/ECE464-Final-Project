"""list cover_url and group_name

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lists', sa.Column('cover_url',  sa.String(),      nullable=True))
    op.add_column('lists', sa.Column('group_name', sa.String(100),   nullable=True))


def downgrade() -> None:
    op.drop_column('lists', 'group_name')
    op.drop_column('lists', 'cover_url')
