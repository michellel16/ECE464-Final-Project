"""spotify integration

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-09 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── artists: add spotify_id ──────────────────────────────────────────────
    op.add_column("artists", sa.Column("spotify_id", sa.String(100), nullable=True))
    op.create_index("ix_artists_spotify_id", "artists", ["spotify_id"])

    # ── albums: add spotify_id ───────────────────────────────────────────────
    op.add_column("albums", sa.Column("spotify_id", sa.String(100), nullable=True))
    op.create_index("ix_albums_spotify_id", "albums", ["spotify_id"])

    # ── songs: add spotify columns + audio features ──────────────────────────
    op.add_column("songs", sa.Column("spotify_id",          sa.String(100), nullable=True))
    op.add_column("songs", sa.Column("spotify_preview_url", sa.String(),    nullable=True))
    op.add_column("songs", sa.Column("danceability",        sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("energy",              sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("valence",             sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("loudness",            sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("tempo",               sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("acousticness",        sa.Float(),     nullable=True))
    op.add_column("songs", sa.Column("instrumentalness",    sa.Float(),     nullable=True))
    op.create_index("ix_songs_spotify_id", "songs", ["spotify_id"])

    # ── users: add spotify OAuth columns ────────────────────────────────────
    op.add_column("users", sa.Column("spotify_id",               sa.String(100), nullable=True))
    op.add_column("users", sa.Column("spotify_access_token",     sa.String(),    nullable=True))
    op.add_column("users", sa.Column("spotify_refresh_token",    sa.String(),    nullable=True))
    op.add_column("users", sa.Column("spotify_token_expires_at", sa.DateTime(),  nullable=True))
    op.add_column("users", sa.Column("spotify_display_name",     sa.String(100), nullable=True))
    op.add_column("users", sa.Column("spotify_image_url",        sa.String(),    nullable=True))


def downgrade() -> None:
    op.drop_index("ix_songs_spotify_id",   table_name="songs")
    op.drop_index("ix_albums_spotify_id",  table_name="albums")
    op.drop_index("ix_artists_spotify_id", table_name="artists")

    op.drop_column("users", "spotify_image_url")
    op.drop_column("users", "spotify_display_name")
    op.drop_column("users", "spotify_token_expires_at")
    op.drop_column("users", "spotify_refresh_token")
    op.drop_column("users", "spotify_access_token")
    op.drop_column("users", "spotify_id")

    op.drop_column("songs", "instrumentalness")
    op.drop_column("songs", "acousticness")
    op.drop_column("songs", "tempo")
    op.drop_column("songs", "loudness")
    op.drop_column("songs", "valence")
    op.drop_column("songs", "energy")
    op.drop_column("songs", "danceability")
    op.drop_column("songs", "spotify_preview_url")
    op.drop_column("songs", "spotify_id")

    op.drop_column("albums", "spotify_id")
    op.drop_column("artists", "spotify_id")
