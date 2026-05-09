import os
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .seed import seed_database
from .routers import auth, users, music, lists, social, search, stats, spotify, recommendations, charts, notifications

STATIC_DIR = Path(__file__).parent / "static"
AVATARS_DIR = STATIC_DIR / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Tunelog API", version="1.0.0")

_origins = ["http://localhost:5173", "http://localhost:3000"]
_frontend_url = os.environ.get("FRONTEND_URL", "").strip().rstrip("/")
if _frontend_url and _frontend_url not in _origins:
    _origins.append(_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(music.router)
app.include_router(lists.router)
app.include_router(social.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(spotify.router)
app.include_router(recommendations.router)
app.include_router(charts.router)
app.include_router(notifications.router)


async def _backfill_images():
    """On startup, fetch missing artist images / album covers from Spotify."""
    from .database import SessionLocal
    from . import models
    from .routers.search import _enrich_missing_images

    db = SessionLocal()
    try:
        from sqlalchemy import or_
        artists = db.query(models.Artist).filter(
            or_(
                models.Artist.image_url.is_(None),
                models.Artist.image_url.like("%wikimedia%"),
                models.Artist.image_url.like("%wikipedia%"),
            )
        ).all()
        albums = db.query(models.Album).filter(
            or_(
                models.Album.cover_url.is_(None),
                models.Album.cover_url.like("%wikimedia%"),
                models.Album.cover_url.like("%wikipedia%"),
            )
        ).all()
        if artists or albums:
            print(f"[startup] Fetching images for {len(artists)} artist(s) and {len(albums)} album(s)…")
            await _enrich_missing_images(db, artists, albums)
            print("[startup] Image backfill complete.")
    except Exception as e:
        print(f"[startup] Image backfill skipped: {e}")
    finally:
        db.close()


def _wait_for_db(timeout: int = 30) -> bool:
    """Wait up to `timeout` seconds for the database to accept connections."""
    from .database import engine
    from sqlalchemy import text
    for i in range(timeout):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            print(f"[startup] Waiting for database… ({i+1}/{timeout})")
            time.sleep(1)
    print("[startup] Database not ready after timeout, continuing anyway.")
    return False


async def _startup_tasks():
    """All heavy startup work runs here in a background task so the server
    starts accepting requests immediately instead of blocking for DB calls."""
    import asyncio
    from .database import SessionLocal
    from sqlalchemy import text

    _wait_for_db(timeout=10)

    try:
        seed_database()
    except Exception as e:
        print(f"Seed skipped: {e}")

    try:
        from .routers.charts import _do_propagate_genres, _do_cleanup_genres
        _db = SessionLocal()
        try:
            already = _db.execute(text("SELECT 1 FROM artist_genre LIMIT 1")).fetchone()
            if not already:
                prop = _do_propagate_genres(_db)
                removed = _do_cleanup_genres(_db)
                print(f"[startup] Genres: tagged {prop['artists_tagged']} artist(s), {prop['albums_tagged']} album(s); removed {removed} unused genre(s)")
        finally:
            _db.close()
    except Exception as e:
        print(f"[startup] Genre sync skipped: {e}")

    try:
        from .routers.charts import _do_fix_genres
        _db = SessionLocal()
        try:
            result = _do_fix_genres(_db)
            if result["removed"]:
                print(f"[startup] Genre fix: {result['merges']} merged, {result['splits']} split, {result['removed']} removed")
        finally:
            _db.close()
    except Exception as e:
        print(f"[startup] Genre fix skipped: {e}")

    await _backfill_images()


@app.on_event("startup")
async def on_startup():
    import asyncio
    asyncio.create_task(_startup_tasks())


@app.get("/api")
def root():
    return {"message": "Tunelog API is running"}
