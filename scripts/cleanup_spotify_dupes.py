"""
Clean up all duplicate artists and albums sharing the same spotify_id.
For each group: keep the lowest id (original import), delete the rest.
Then apply the unique index migration.
"""
import os, sys
from pathlib import Path
from sqlalchemy import create_engine, text

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DATABASE_URL = os.environ.get("APP_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    sys.exit("Set DATABASE_URL first")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
if "sslmode=" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

engine = create_engine(DATABASE_URL)


def delete_artist_ids(conn, ids_to_delete):
    for artist_id in ids_to_delete:
        name = conn.execute(text("SELECT name FROM artists WHERE id=:id"), {"id": artist_id}).scalar()
        print(f"  Deleting artist id={artist_id} ({name!r})")
        conn.execute(text("DELETE FROM reviews WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
        conn.execute(text("DELETE FROM reviews WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
        conn.execute(text("DELETE FROM user_song_statuses WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
        conn.execute(text("DELETE FROM user_album_statuses WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
        conn.execute(text("DELETE FROM list_items WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
        conn.execute(text("DELETE FROM list_items WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
        conn.execute(text("DELETE FROM activities WHERE target_type='song' AND target_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
        conn.execute(text("DELETE FROM activities WHERE target_type='album' AND target_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
        conn.execute(text("DELETE FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
        conn.execute(text("DELETE FROM albums WHERE artist_id=:id"), {"id": artist_id})
        conn.execute(text("DELETE FROM artist_genre WHERE artist_id=:id"), {"id": artist_id})
        conn.execute(text("DELETE FROM artists WHERE id=:id"), {"id": artist_id})


def delete_album_ids(conn, ids_to_delete):
    for album_id in ids_to_delete:
        title = conn.execute(text("SELECT title FROM albums WHERE id=:id"), {"id": album_id}).scalar()
        print(f"  Deleting album id={album_id} ({title!r})")
        conn.execute(text("DELETE FROM reviews WHERE song_id IN (SELECT id FROM songs WHERE album_id=:id)"), {"id": album_id})
        conn.execute(text("DELETE FROM reviews WHERE album_id=:id"), {"id": album_id})
        conn.execute(text("DELETE FROM user_song_statuses WHERE song_id IN (SELECT id FROM songs WHERE album_id=:id)"), {"id": album_id})
        conn.execute(text("DELETE FROM user_album_statuses WHERE album_id=:id"), {"id": album_id})
        conn.execute(text("DELETE FROM list_items WHERE song_id IN (SELECT id FROM songs WHERE album_id=:id)"), {"id": album_id})
        conn.execute(text("DELETE FROM list_items WHERE album_id=:id"), {"id": album_id})
        conn.execute(text("DELETE FROM songs WHERE album_id=:id"), {"id": album_id})
        conn.execute(text("DELETE FROM album_genre WHERE album_id=:id"), {"id": album_id})
        conn.execute(text("DELETE FROM albums WHERE id=:id"), {"id": album_id})


with engine.begin() as conn:
    # ── 1. Duplicate artists by spotify_id ──────────────────────────────────
    print("=== Cleaning duplicate artists ===")
    artist_dupes = conn.execute(text("""
        SELECT spotify_id, array_agg(id ORDER BY id) as ids
        FROM artists WHERE spotify_id IS NOT NULL
        GROUP BY spotify_id HAVING COUNT(*) > 1
    """)).fetchall()

    for spotify_id, ids in artist_dupes:
        keep = ids[0]  # lowest id = original import
        to_delete = ids[1:]
        name = conn.execute(text("SELECT name FROM artists WHERE id=:id"), {"id": keep}).scalar()
        print(f"  spotify_id={spotify_id}: keep id={keep} ({name!r}), delete {to_delete}")
        delete_artist_ids(conn, to_delete)

    # ── 2. Duplicate albums by spotify_id (remaining after artist cleanup) ──
    print("\n=== Cleaning duplicate albums ===")
    album_dupes = conn.execute(text("""
        SELECT spotify_id, array_agg(id ORDER BY id) as ids
        FROM albums WHERE spotify_id IS NOT NULL
        GROUP BY spotify_id HAVING COUNT(*) > 1
    """)).fetchall()

    for spotify_id, ids in album_dupes:
        keep = ids[0]
        to_delete = ids[1:]
        title = conn.execute(text("SELECT title FROM albums WHERE id=:id"), {"id": keep}).scalar()
        print(f"  spotify_id={spotify_id}: keep id={keep} ({title!r}), delete {to_delete}")
        delete_album_ids(conn, to_delete)

    # ── 3. Verify clean ─────────────────────────────────────────────────────
    print("\n=== Verifying ===")
    remaining_artist_dupes = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT spotify_id FROM artists WHERE spotify_id IS NOT NULL
            GROUP BY spotify_id HAVING COUNT(*) > 1
        ) x
    """)).scalar()
    remaining_album_dupes = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT spotify_id FROM albums WHERE spotify_id IS NOT NULL
            GROUP BY spotify_id HAVING COUNT(*) > 1
        ) x
    """)).scalar()
    print(f"  Remaining artist spotify_id dupes: {remaining_artist_dupes}")
    print(f"  Remaining album spotify_id dupes:  {remaining_album_dupes}")

print("\nAll done. Now run: uv run alembic upgrade head")
