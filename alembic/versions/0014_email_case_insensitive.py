"""email case-insensitive unique index

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-09
"""
from alembic import op

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE UNIQUE INDEX ix_users_email_lower ON users (lower(email))"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
