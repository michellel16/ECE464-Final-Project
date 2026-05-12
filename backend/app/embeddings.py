"""
Embedding generation utilities using OpenAI text-embedding-3-small (1536 dims).

Vectors are stored in pgvector columns on Artist, Album, and Song.
Text is built from all available semantic signals: name, bio, description,
genres, audio features, and user review text.
"""
import asyncio
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Allow up to 5 concurrent OpenAI calls (paid tier supports 500 RPM).
_openai_sem = asyncio.Semaphore(5)

# Limit concurrent background embedding tasks to 1 so they don't pile up
# DB connections and exhaust the Supabase session-mode pool.
_bg_embed_sem = asyncio.Semaphore(1)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Positive cache: identical text → identical vector (no need to re-call OpenAI).
# Capped at 2000 entries; oldest entry is evicted when full.
_CACHE_MAX = 2000
_embedding_cache: dict[str, list[float]] = {}

# Negative cache: texts that recently failed get a cooldown so they are not
# retried on every request.  After _FAILURE_COOLDOWN_SECS the entry expires
# and the next caller may try again (rate limit may have reset by then).
_FAILURE_COOLDOWN_SECS = 600  # 10 minutes
_embedding_failure_times: dict[str, float] = {}  # text → monotonic timestamp of last failure


def is_embedding_cooling_down(text: str) -> bool:
    """Return True if this text failed recently and should not be retried yet."""
    t = _embedding_failure_times.get(text)
    return t is not None and (time.monotonic() - t) < _FAILURE_COOLDOWN_SECS


# ── Text builders ─────────────────────────────────────────────────────────────

def artist_text(artist) -> str:
    parts = [artist.name]
    if artist.bio:
        parts.append(artist.bio)
    genres = [g.name for g in (artist.genres or [])]
    if genres:
        parts.append(f"Genres: {', '.join(genres)}")
    if artist.country:
        parts.append(f"Country: {artist.country}")
    if artist.formed_year:
        parts.append(f"Formed: {artist.formed_year}")
    return ". ".join(p for p in parts if p)


def album_text(album) -> str:
    artist_name = album.artist.name if album.artist else ""
    parts = [f"{album.title} by {artist_name}" if artist_name else album.title]
    if album.description:
        parts.append(album.description)
    genres = [g.name for g in (album.genres or [])]
    if genres:
        parts.append(f"Genres: {', '.join(genres)}")
    if album.release_date:
        parts.append(f"Released: {str(album.release_date)[:4]}")
    review_texts = [r.text for r in (album.reviews or []) if r.text]
    if review_texts:
        parts.append("Listener reviews: " + " | ".join(review_texts[:5]))
    return ". ".join(p for p in parts if p)


def song_text(song) -> str:
    artist_name = song.artist.name if song.artist else ""
    parts = [f"{song.title} by {artist_name}" if artist_name else song.title]
    if song.album:
        parts.append(f"from the album {song.album.title}")
    genres = [g.name for g in (song.artist.genres or [])] if song.artist else []
    if genres:
        parts.append(f"Genres: {', '.join(genres)}")
    # Translate Spotify audio features into natural-language descriptors
    descriptors = []
    if song.energy is not None:
        if song.energy > 0.75:
            descriptors.append("high energy")
        elif song.energy < 0.3:
            descriptors.append("low energy")
    if song.valence is not None:
        if song.valence > 0.7:
            descriptors.append("upbeat and positive")
        elif song.valence < 0.3:
            descriptors.append("melancholic and dark")
    if song.danceability is not None and song.danceability > 0.7:
        descriptors.append("danceable")
    if song.acousticness is not None and song.acousticness > 0.7:
        descriptors.append("acoustic")
    if song.instrumentalness is not None and song.instrumentalness > 0.5:
        descriptors.append("instrumental")
    if song.tempo is not None:
        if song.tempo > 150:
            descriptors.append("fast tempo")
        elif song.tempo < 70:
            descriptors.append("slow tempo")
    if descriptors:
        parts.append(", ".join(descriptors))
    review_texts = [r.text for r in (song.reviews or []) if r.text]
    if review_texts:
        parts.append("Listener reviews: " + " | ".join(review_texts[:5]))
    return ". ".join(p for p in parts if p)


# ── OpenAI API call ───────────────────────────────────────────────────────────

async def get_embedding(text: str) -> Optional[list[float]]:
    """Call OpenAI embeddings API and return a 1536-d vector, or None on failure.

    Results are cached in memory so repeated searches for the same text never
    re-hit the API. All calls are serialised through _openai_sem so concurrent
    requests from multiple users can't pile up and trigger cascading 429s.
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set — skipping embedding generation")
        return None
    text = text.strip()
    if not text:
        return None

    if text in _embedding_cache:
        return _embedding_cache[text]

    # Fast-fail: this text failed recently — don't hammer the API again.
    if is_embedding_cooling_down(text):
        logger.debug("Embedding cooling down — skipping OpenAI call")
        return None

    async with _openai_sem:
        # Re-check after acquiring the lock: a queued waiter may have fetched/failed it.
        if text in _embedding_cache:
            return _embedding_cache[text]
        if is_embedding_cooling_down(text):
            return None

        for attempt in range(5):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                        json={"model": EMBEDDING_MODEL, "input": text},
                    )
                if resp.status_code == 429:
                    if attempt == 4:
                        logger.warning("OpenAI rate limited — giving up; cooling down for %ds", _FAILURE_COOLDOWN_SECS)
                        _embedding_failure_times[text] = time.monotonic()
                        return None
                    # Honour the Retry-After header when present (OpenAI sends it).
                    raw = resp.headers.get("retry-after") or resp.headers.get("x-ratelimit-reset-requests")
                    try:
                        wait = float(raw) if raw else 2 ** (attempt + 2)
                    except (TypeError, ValueError):
                        wait = 2 ** (attempt + 2)
                    wait = min(wait, 60.0)  # cap at 60 s
                    logger.warning("OpenAI rate limited — retrying in %.0fs", wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                vec = resp.json()["data"][0]["embedding"]
                if len(_embedding_cache) >= _CACHE_MAX:
                    _embedding_cache.pop(next(iter(_embedding_cache)))
                _embedding_cache[text] = vec
                _embedding_failure_times.pop(text, None)  # clear any prior failure
                return vec
            except Exception as exc:
                logger.error("OpenAI embedding error: %s", exc)
                _embedding_failure_times[text] = time.monotonic()
                return None
    return None


# ── Inline helpers (caller provides db session) ───────────────────────────────

async def embed_and_save_artist(artist, db) -> None:
    vec = await get_embedding(artist_text(artist))
    if vec is not None:
        artist.embedding = vec
        db.commit()


async def embed_and_save_album(album, db) -> None:
    vec = await get_embedding(album_text(album))
    if vec is not None:
        album.embedding = vec
        db.commit()


async def embed_and_save_song(song, db) -> None:
    vec = await get_embedding(song_text(song))
    if vec is not None:
        song.embedding = vec
        db.commit()


# ── Background-task helpers (create their own DB session) ─────────────────────
# Use these when the original request session may have already closed.

async def reembed_artist_bg(artist_id: int) -> None:
    async with _bg_embed_sem:
        from .database import SessionLocal
        from . import models
        from sqlalchemy.orm import joinedload

        # Step 1: read — brief DB use.
        db = SessionLocal()
        try:
            artist = (
                db.query(models.Artist)
                .options(joinedload(models.Artist.genres))
                .filter(models.Artist.id == artist_id)
                .first()
            )
            text = artist_text(artist) if artist else None
        except Exception as exc:
            logger.error("Background embed_artist(%d) read failed: %s", artist_id, exc)
            return
        finally:
            db.close()  # release before OpenAI call

        if not text:
            return

        # Step 2: embed — no DB connection held during potential rate-limit sleeps.
        vec = await get_embedding(text)
        if vec is None:
            return

        # Step 3: write — brief DB use.
        db = SessionLocal()
        try:
            artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
            if artist:
                artist.embedding = vec
                db.commit()
        except Exception as exc:
            logger.error("Background embed_artist(%d) write failed: %s", artist_id, exc)
        finally:
            db.close()


async def reembed_album_bg(album_id: int) -> None:
    async with _bg_embed_sem:
        from .database import SessionLocal
        from . import models
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        try:
            album = (
                db.query(models.Album)
                .options(
                    joinedload(models.Album.artist).joinedload(models.Artist.genres),
                    joinedload(models.Album.genres),
                    joinedload(models.Album.reviews),
                )
                .filter(models.Album.id == album_id)
                .first()
            )
            text = album_text(album) if album else None
        except Exception as exc:
            logger.error("Background embed_album(%d) read failed: %s", album_id, exc)
            return
        finally:
            db.close()

        if not text:
            return

        vec = await get_embedding(text)
        if vec is None:
            return

        db = SessionLocal()
        try:
            album = db.query(models.Album).filter(models.Album.id == album_id).first()
            if album:
                album.embedding = vec
                db.commit()
        except Exception as exc:
            logger.error("Background embed_album(%d) write failed: %s", album_id, exc)
        finally:
            db.close()


async def reembed_song_bg(song_id: int) -> None:
    async with _bg_embed_sem:
        from .database import SessionLocal
        from . import models
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        try:
            song = (
                db.query(models.Song)
                .options(
                    joinedload(models.Song.artist).joinedload(models.Artist.genres),
                    joinedload(models.Song.album),
                    joinedload(models.Song.reviews),
                )
                .filter(models.Song.id == song_id)
                .first()
            )
            text = song_text(song) if song else None
        except Exception as exc:
            logger.error("Background embed_song(%d) read failed: %s", song_id, exc)
            return
        finally:
            db.close()

        if not text:
            return

        vec = await get_embedding(text)
        if vec is None:
            return

        db = SessionLocal()
        try:
            song = db.query(models.Song).filter(models.Song.id == song_id).first()
            if song:
                song.embedding = vec
                db.commit()
        except Exception as exc:
            logger.error("Background embed_song(%d) write failed: %s", song_id, exc)
        finally:
            db.close()
