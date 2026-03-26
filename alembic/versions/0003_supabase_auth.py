"""supabase auth integration

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-25 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("supabase_id", sa.String(36), nullable=True))
    op.create_index("ix_users_supabase_id", "users", ["supabase_id"], unique=True)
    op.alter_column("users", "hashed_password", nullable=True)


def downgrade() -> None:
    op.alter_column("users", "hashed_password", nullable=False)
    op.drop_index("ix_users_supabase_id", table_name="users")
    op.drop_column("users", "supabase_id")
