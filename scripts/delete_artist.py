"""Delete an artist and all related data by name fragment."""
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

QUERY = "%Beyonc%"

def review_count(conn, artist_id):
    return conn.execute(text("""
        SELECT COUNT(*) FROM reviews
        WHERE song_id  IN (SELECT id FROM songs WHERE artist_id=:id
                           OR album_id IN (SELECT id FROM albums WHERE artist_id=:id))
           OR album_id IN (SELECT id FROM albums WHERE artist_id=:id)
    """), {"id": artist_id}).scalar() or 0

def delete_artist(conn, artist_id, name):
    print(f"Deleting: id={artist_id}  name={name!r}")
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
    print("  Done.")

with engine.begin() as conn:
    rows = conn.execute(text("SELECT id, name FROM artists WHERE name ILIKE :q"), {"q": QUERY}).fetchall()
    if not rows:
        print("No matching artists found.")
        sys.exit(0)

    if len(rows) == 1:
        delete_artist(conn, rows[0][0], rows[0][1])
    else:
        counts = [(aid, name, review_count(conn, aid)) for aid, name in rows]
        for aid, name, cnt in counts:
            print(f"  id={aid}  name={name!r}  reviews={cnt}")
        to_delete = min(counts, key=lambda x: x[2])
        print(f"Keeping higher-review entry; deleting id={to_delete[0]}  name={to_delete[1]!r}  reviews={to_delete[2]}")
        delete_artist(conn, to_delete[0], to_delete[1])

print("All done.")
