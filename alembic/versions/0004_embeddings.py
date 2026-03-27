"""add pgvector embeddings to artists, albums, songs

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-26 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 1536


def upgrade() -> None:
    # Enable the pgvector extension (Supabase has this available by default)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding columns
    op.execute(f"ALTER TABLE artists ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM})")
    op.execute(f"ALTER TABLE albums  ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM})")
    op.execute(f"ALTER TABLE songs   ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM})")

    # HNSW indexes for fast approximate cosine similarity search.
    # ef_construction=64, m=16 are sensible defaults for datasets < 1M rows.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_artists_embedding "
        "ON artists USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_albums_embedding "
        "ON albums USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_songs_embedding "
        "ON songs USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_artists_embedding")
    op.execute("DROP INDEX IF EXISTS ix_albums_embedding")
    op.execute("DROP INDEX IF EXISTS ix_songs_embedding")
    op.execute("ALTER TABLE artists DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE albums  DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE songs   DROP COLUMN IF EXISTS embedding")
