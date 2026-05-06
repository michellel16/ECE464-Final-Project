"""add list likes

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: str = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "list_likes",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("list_id", sa.Integer, sa.ForeignKey("lists.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("list_likes")
