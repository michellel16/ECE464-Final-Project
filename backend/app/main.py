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


@app.on_event("startup")
async def on_startup():
    # Seed only if the database is empty (tables must exist — run migrations first)
    try:
        seed_database()
    except Exception as e:
        print(f"Seed skipped: {e}")


@app.get("/api")
def root():
    return {"message": "Tunelog API is running"}
