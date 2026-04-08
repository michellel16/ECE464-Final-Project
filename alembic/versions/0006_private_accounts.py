"""add private accounts and follow requests

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_private", sa.Boolean(), server_default="false", nullable=False))

    op.create_table(
        "follow_requests",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("requester_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id",    sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at",   sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_follow_requests_target", "follow_requests", ["target_id"])
    op.create_unique_constraint("uq_follow_requests_pair", "follow_requests", ["requester_id", "target_id"])


def downgrade() -> None:
    op.drop_constraint("uq_follow_requests_pair", "follow_requests", type_="unique")
    op.drop_index("ix_follow_requests_target", table_name="follow_requests")
    op.drop_table("follow_requests")
    op.drop_column("users", "is_private")
