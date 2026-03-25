from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .seed import seed_database
from .routers import auth, users, music, lists, social, search, stats, spotify

STATIC_DIR = Path(__file__).parent / "static"
AVATARS_DIR = STATIC_DIR / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Tunelog API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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


@app.on_event("startup")
async def on_startup():
    # Seed only if the database is empty (tables must exist — run migrations first)
    try:
        seed_database()
    except Exception as e:
        print(f"Seed skipped: {e}")

    await _backfill_images()


@app.get("/api")
def root():
    return {"message": "Tunelog API is running"}
