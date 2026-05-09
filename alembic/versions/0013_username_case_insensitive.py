"""username case-insensitive unique index

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-09
"""
from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE UNIQUE INDEX ix_users_username_lower ON users (lower(username))"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_username_lower")
