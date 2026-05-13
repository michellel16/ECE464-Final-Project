"""Unique partial indexes on spotify_id for artists, albums, songs

Revision ID: 0017
Revises: 0016
Create Date: 2026-05-12
"""
from alembic import op

revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_artists_spotify_id
        ON artists(spotify_id)
        WHERE spotify_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_albums_spotify_id
        ON albums(spotify_id)
        WHERE spotify_id IS NOT NULL
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_songs_spotify_id
        ON songs(spotify_id)
        WHERE spotify_id IS NOT NULL
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_artists_spotify_id")
    op.execute("DROP INDEX IF EXISTS uq_albums_spotify_id")
    op.execute("DROP INDEX IF EXISTS uq_songs_spotify_id")
