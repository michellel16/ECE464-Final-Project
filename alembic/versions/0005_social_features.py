"""add review likes and user recommendations

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_likes",
        sa.Column("user_id",    sa.Integer, sa.ForeignKey("users.id",   ondelete="CASCADE"), primary_key=True),
        sa.Column("review_id",  sa.Integer, sa.ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_recommendations",
        sa.Column("id",           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sender_id",    sa.Integer, sa.ForeignKey("users.id",   ondelete="CASCADE"),   nullable=False),
        sa.Column("recipient_id", sa.Integer, sa.ForeignKey("users.id",   ondelete="CASCADE"),   nullable=False),
        sa.Column("song_id",      sa.Integer, sa.ForeignKey("songs.id",   ondelete="SET NULL"),  nullable=True),
        sa.Column("album_id",     sa.Integer, sa.ForeignKey("albums.id",  ondelete="SET NULL"),  nullable=True),
        sa.Column("note",         sa.Text,    nullable=True),
        sa.Column("is_read",      sa.Boolean, server_default="false",     nullable=False),
        sa.Column("created_at",   sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_recs_recipient", "user_recommendations", ["recipient_id"])


def downgrade() -> None:
    op.drop_index("ix_user_recs_recipient", table_name="user_recommendations")
    op.drop_table("user_recommendations")
    op.drop_table("review_likes")
