"""Find all duplicate artists and delete the weaker copies.

Keeps the entry that:
  1. Has a spotify_id (Spotify-imported), OR
  2. Has more reviews across all songs/albums.
  Tiebreak: higher artist id (more recently added, likely the import).
"""
import os, sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Load .env from project root
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


def review_count(conn, artist_id):
    return conn.execute(text("""
        SELECT COUNT(*) FROM reviews
        WHERE song_id  IN (SELECT id FROM songs WHERE artist_id=:id
                           OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))
           OR album_id IN (SELECT id FROM albums WHERE artist_id=:id)
    """), {"id": artist_id}).scalar() or 0


def delete_artist(conn, artist_id, name):
    conn.execute(text("DELETE FROM reviews WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
    conn.execute(text("DELETE FROM reviews WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
    conn.execute(text("DELETE FROM user_song_statuses WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
    conn.execute(text("DELETE FROM user_album_statuses WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
    conn.execute(text("DELETE FROM list_items WHERE song_id IN (SELECT id FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))"), {"id": artist_id})
    conn.execute(text("DELETE FROM list_items WHERE album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
    conn.execute(text("DELETE FROM songs WHERE artist_id=:id OR album_id IN (SELECT id FROM albums WHERE artist_id=:id)"), {"id": artist_id})
    conn.execute(text("DELETE FROM albums WHERE artist_id=:id"), {"id": artist_id})
    conn.execute(text("DELETE FROM artist_genre WHERE artist_id=:id"), {"id": artist_id})
    conn.execute(text("DELETE FROM artists WHERE id=:id"), {"id": artist_id})


with engine.begin() as conn:
    # Find all names that appear more than once (case-insensitive)
    dupes = conn.execute(text("""
        SELECT LOWER(name) AS lower_name, COUNT(*) AS cnt
        FROM artists
        GROUP BY LOWER(name)
        HAVING COUNT(*) > 1
        ORDER BY lower_name
    """)).fetchall()

    if not dupes:
        print("No duplicate artists found.")
        sys.exit(0)

    print(f"Found {len(dupes)} duplicate artist name(s):\n")

    for lower_name, cnt in dupes:
        rows = conn.execute(text(
            "SELECT id, name, spotify_id FROM artists WHERE LOWER(name)=:n ORDER BY id"
        ), {"n": lower_name}).fetchall()

        # Score each: (has_spotify, review_count, id) — higher = better
        scored = []
        for aid, name, spotify_id in rows:
            rc = review_count(conn, aid)
            scored.append((aid, name, spotify_id, rc))
            print(f"  id={aid:5d}  spotify={'yes' if spotify_id else 'no ':3}  reviews={rc:4d}  name={name!r}")

        # Pick winner: prefer spotify_id, then most reviews, then highest id
        winner = max(scored, key=lambda x: (x[2] is not None, x[3], x[0]))
        losers = [s for s in scored if s[0] != winner[0]]

        print(f"  -> KEEP id={winner[0]} ({winner[1]!r}), DELETE {[s[0] for s in losers]}")
        for loser in losers:
            delete_artist(conn, loser[0], loser[1])
        print()

print("All done.")
