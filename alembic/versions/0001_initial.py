"""initial

Revision ID: 0001
Revises:
Create Date: 2026-03-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── genres ──────────────────────────────────────────────────────────────
    op.create_table(
        "genres",
        sa.Column("id",   sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )

    # ── artists ──────────────────────────────────────────────────────────────
    op.create_table(
        "artists",
        sa.Column("id",          sa.Integer(), primary_key=True),
        sa.Column("name",        sa.String(100), nullable=False),
        sa.Column("bio",         sa.Text(),      nullable=True),
        sa.Column("image_url",   sa.String(),    nullable=True),
        sa.Column("formed_year", sa.Integer(),   nullable=True),
        sa.Column("country",     sa.String(50),  nullable=True),
    )
    op.create_index("ix_artists_name", "artists", ["name"])

    # ── albums ───────────────────────────────────────────────────────────────
    op.create_table(
        "albums",
        sa.Column("id",           sa.Integer(), primary_key=True),
        sa.Column("title",        sa.String(200), nullable=False),
        sa.Column("artist_id",    sa.Integer(), sa.ForeignKey("artists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("release_date", sa.String(20),  nullable=True),
        sa.Column("cover_url",    sa.String(),     nullable=True),
        sa.Column("description",  sa.Text(),       nullable=True),
    )
    op.create_index("ix_albums_title",     "albums", ["title"])
    op.create_index("ix_albums_artist_id", "albums", ["artist_id"])

    # ── songs ────────────────────────────────────────────────────────────────
    op.create_table(
        "songs",
        sa.Column("id",               sa.Integer(), primary_key=True),
        sa.Column("title",            sa.String(200), nullable=False),
        sa.Column("artist_id",        sa.Integer(), sa.ForeignKey("artists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("album_id",         sa.Integer(), sa.ForeignKey("albums.id",  ondelete="SET NULL"), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("track_number",     sa.Integer(), nullable=True),
    )
    op.create_index("ix_songs_title",     "songs", ["title"])
    op.create_index("ix_songs_artist_id", "songs", ["artist_id"])

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              sa.Integer(), primary_key=True),
        sa.Column("username",        sa.String(50),  nullable=False, unique=True),
        sa.Column("email",           sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(),    nullable=False),
        sa.Column("bio",             sa.Text(),      nullable=True),
        sa.Column("avatar_url",      sa.String(),    nullable=True),
        sa.Column("created_at",      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column("is_active",       sa.Boolean(),   nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email",    "users", ["email"],    unique=True)

    # ── artist_genre (many-to-many) ──────────────────────────────────────────
    op.create_table(
        "artist_genre",
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id",  sa.Integer(), sa.ForeignKey("genres.id",  ondelete="CASCADE"), primary_key=True),
    )

    # ── album_genre (many-to-many) ───────────────────────────────────────────
    op.create_table(
        "album_genre",
        sa.Column("album_id", sa.Integer(), sa.ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.Integer(), sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )

    # ── user_follows ─────────────────────────────────────────────────────────
    op.create_table(
        "user_follows",
        sa.Column("follower_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("followed_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at",  sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── activities ───────────────────────────────────────────────────────────
    op.create_table(
        "activities",
        sa.Column("id",          sa.Integer(), primary_key=True),
        sa.Column("user_id",     sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(60), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id",   sa.Integer(),  nullable=True),
        sa.Column("meta",        sa.Text(),     nullable=True),
        sa.Column("created_at",  sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_activities_user_id",    "activities", ["user_id"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])

    # ── reviews ──────────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id",         sa.Integer(), primary_key=True),
        sa.Column("user_id",    sa.Integer(), sa.ForeignKey("users.id",  ondelete="CASCADE"), nullable=False),
        sa.Column("song_id",    sa.Integer(), sa.ForeignKey("songs.id",  ondelete="CASCADE"), nullable=True),
        sa.Column("album_id",   sa.Integer(), sa.ForeignKey("albums.id", ondelete="CASCADE"), nullable=True),
        sa.Column("text",       sa.Text(),    nullable=True),
        sa.Column("rating",     sa.Float(),   nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rating >= 0.5 AND rating <= 5.0", name="ck_reviews_rating_range"),
        sa.CheckConstraint("(song_id IS NOT NULL) != (album_id IS NOT NULL)", name="ck_reviews_one_target"),
    )
    op.create_index("ix_reviews_user_id",  "reviews", ["user_id"])
    op.create_index("ix_reviews_album_id", "reviews", ["album_id"])
    op.create_index("ix_reviews_song_id",  "reviews", ["song_id"])
    # Enforce one review per user per song/album
    op.create_index("uq_reviews_user_album", "reviews", ["user_id", "album_id"],
                    unique=True, postgresql_where=sa.text("album_id IS NOT NULL"))
    op.create_index("uq_reviews_user_song",  "reviews", ["user_id", "song_id"],
                    unique=True, postgresql_where=sa.text("song_id IS NOT NULL"))

    # ── lists ─────────────────────────────────────────────────────────────────
    op.create_table(
        "lists",
        sa.Column("id",          sa.Integer(), primary_key=True),
        sa.Column("user_id",     sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",        sa.String(100), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        sa.Column("list_type",   sa.String(50),  nullable=False, server_default="custom"),
        sa.Column("is_public",   sa.Boolean(),   nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lists_user_id", "lists", ["user_id"])

    # ── list_items ───────────────────────────────────────────────────────────
    op.create_table(
        "list_items",
        sa.Column("id",       sa.Integer(), primary_key=True),
        sa.Column("list_id",  sa.Integer(), sa.ForeignKey("lists.id",  ondelete="CASCADE"), nullable=False),
        sa.Column("song_id",  sa.Integer(), sa.ForeignKey("songs.id",  ondelete="CASCADE"), nullable=True),
        sa.Column("album_id", sa.Integer(), sa.ForeignKey("albums.id", ondelete="CASCADE"), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("notes",    sa.Text(),     nullable=True),
    )
    op.create_index("ix_list_items_list_id", "list_items", ["list_id"])

    # ── user_song_statuses ────────────────────────────────────────────────────
    op.create_table(
        "user_song_statuses",
        sa.Column("user_id",    sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("song_id",    sa.Integer(), sa.ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status",     sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('listened', 'want_to_listen', 'favorites')",
            name="ck_user_song_status_valid",
        ),
    )

    # ── user_album_statuses ───────────────────────────────────────────────────
    op.create_table(
        "user_album_statuses",
        sa.Column("user_id",    sa.Integer(), sa.ForeignKey("users.id",  ondelete="CASCADE"), primary_key=True),
        sa.Column("album_id",   sa.Integer(), sa.ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status",     sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('listened', 'want_to_listen', 'favorites')",
            name="ck_user_album_status_valid",
        ),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("user_album_statuses")
    op.drop_table("user_song_statuses")
    op.drop_table("list_items")
    op.drop_table("lists")
    op.drop_table("reviews")
    op.drop_table("activities")
    op.drop_table("user_follows")
    op.drop_table("album_genre")
    op.drop_table("artist_genre")
    op.drop_table("users")
    op.drop_table("songs")
    op.drop_table("albums")
    op.drop_table("artists")
    op.drop_table("genres")
