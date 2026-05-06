"""add taste embedding and profile hash to users

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0007"
down_revision: str = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("taste_embedding", Vector(1536), nullable=True))
    op.add_column("users", sa.Column("taste_profile_hash", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "taste_profile_hash")
    op.drop_column("users", "taste_embedding")
