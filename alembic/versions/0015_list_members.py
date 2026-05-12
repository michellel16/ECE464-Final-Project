"""list members for sharing and collaboration

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'list_members',
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role',     sa.String(20), nullable=False, server_default='viewer'),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['list_id'], ['lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('list_id', 'user_id'),
    )


def downgrade():
    op.drop_table('list_members')
