"""Add notifications table

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id',           sa.Integer(),    primary_key=True),
        sa.Column('user_id',      sa.Integer(),    sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type',         sa.String(50),   nullable=False),
        sa.Column('from_user_id', sa.Integer(),    sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('entity_type',  sa.String(50),   nullable=True),
        sa.Column('entity_id',    sa.Integer(),    nullable=True),
        sa.Column('is_read',      sa.Boolean(),    nullable=False, server_default='false'),
        sa.Column('created_at',   sa.DateTime(),   nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
