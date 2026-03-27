import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from .spotify import _get_client_token

router = APIRouter(prefix="/api/search", tags=["search"])


def _sp_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _needs_image(url: str | None) -> bool:
    """Return True if the URL is absent or a Wikipedia hotlink that may not load."""
    if not url:
        return True
    return "wikimedia.org" in url or "wikipedia.org" in url


async def _enrich_missing_images(db: Session, artists: list, albums: list) -> None:
    """
    For any artist/album missing a reliable image/cover (null or Wikipedia URL),
    fetch it from Spotify using client-credentials and persist to DB.
    Runs all requests in parallel; silently ignores Spotify errors.
    """
    artists_todo = [a for a in artists if _needs_image(a.image_url)]
    albums_todo  = [al for al in albums if _needs_image(al.cover_url)]
    if not artists_todo and not albums_todo:
        return

    try:
        token = await _get_client_token()
    except Exception:
        return  # Spotify not configured — skip enrichment

    headers = _sp_headers(token)

    async def enrich_artist(artist: models.Artist, client: httpx.AsyncClient) -> None:
        try:
            if artist.spotify_id:
                r = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist.spotify_id}",
                    headers=headers,
                )
                if r.status_code == 200:
                    images = r.json().get("images") or []
                    if images:
                        artist.image_url = images[0]["url"]
            else:
                r = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": artist.name, "type": "artist", "limit": 1},
                    headers=headers,
                )
                if r.status_code == 200:
                    items = r.json().get("artists", {}).get("items") or []
                    if items:
                        sp = items[0]
                        images = sp.get("images") or []
                        if images:
                            artist.image_url = images[0]["url"]
                        if not artist.spotify_id and sp.get("id"):
                            artist.spotify_id = sp["id"]
        except Exception:
            pass

    async def enrich_album(album: models.Album, client: httpx.AsyncClient) -> None:
        try:
            if album.spotify_id:
                r = await client.get(
                    f"https://api.spotify.com/v1/albums/{album.spotify_id}",
                    headers=headers,
                )
                if r.status_code == 200:
                    images = r.json().get("images") or []
                    if images:
                        album.cover_url = images[0]["url"]
            else:
                artist_name = album.artist.name if album.artist else ""
                query = f"{album.title} {artist_name}".strip()
                r = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": query, "type": "album", "limit": 1},
                    headers=headers,
                )
                if r.status_code == 200:
                    items = r.json().get("albums", {}).get("items") or []
                    if items:
                        sp = items[0]
                        images = sp.get("images") or []
                        if images:
                            album.cover_url = images[0]["url"]
                        if not album.spotify_id and sp.get("id"):
                            album.spotify_id = sp["id"]
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await asyncio.gather(
                *[enrich_artist(a, client) for a in artists_todo],
                *[enrich_album(al, client) for al in albums_todo],
            )
        db.commit()
    except Exception:
        pass


# ── Exact (keyword) search ────────────────────────────────────────────────────

@router.get("/")
async def search(q: str, db: Session = Depends(get_db)):
    like = f"%{q}%"

    artists = db.query(models.Artist).filter(models.Artist.name.ilike(like)).limit(5).all()
    albums  = db.query(models.Album).filter(models.Album.title.ilike(like)).limit(8).all()
    songs   = db.query(models.Song).filter(models.Song.title.ilike(like)).limit(8).all()
    users   = db.query(models.User).filter(models.User.username.ilike(like)).limit(5).all()

    await _enrich_missing_images(db, artists, albums)

    return {
        "artists": [
            {"id": a.id, "name": a.name, "image_url": a.image_url,
             "genres": [g.name for g in a.genres]}
            for a in artists
        ],
        "albums": [
            {
                "id": al.id, "title": al.title, "cover_url": al.cover_url,
                "release_date": al.release_date,
                "artist": {"id": al.artist.id, "name": al.artist.name},
                "genres": [g.name for g in al.genres],
            }
            for al in albums
        ],
        "songs": [
            {
                "id": s.id, "title": s.title,
                "artist": {"id": s.artist.id, "name": s.artist.name},
                "album": {"id": s.album.id, "title": s.album.title, "cover_url": s.album.cover_url} if s.album else None,
            }
            for s in songs
        ],
        "users": [
            {"username": u.username, "avatar_url": u.avatar_url, "bio": u.bio}
            for u in users
        ],
    }


# ── Semantic (vibe) search ────────────────────────────────────────────────────

@router.get("/semantic")
async def semantic_search(q: str, db: Session = Depends(get_db)):
    """
    Embed the query with OpenAI text-embedding-3-small then rank artists,
    albums, and songs by cosine similarity against stored pgvector embeddings.
    """
    from ..embeddings import get_embedding

    vec = await get_embedding(q)
    if vec is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable — check OPENAI_API_KEY",
        )

    # pgvector expects a literal like '[0.1,0.2,...]'
    vec_literal = "[" + ",".join(f"{v:.8f}" for v in vec) + "]"

    artist_rows = db.execute(
        text("""
            SELECT id, name, image_url,
                   1 - (embedding <=> :emb::vector) AS similarity
            FROM artists
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :emb::vector
            LIMIT 5
        """),
        {"emb": vec_literal},
    ).fetchall()

    album_rows = db.execute(
        text("""
            SELECT al.id, al.title, al.cover_url, al.release_date,
                   ar.id   AS artist_id,
                   ar.name AS artist_name,
                   1 - (al.embedding <=> :emb::vector) AS similarity
            FROM albums al
            JOIN artists ar ON ar.id = al.artist_id
            WHERE al.embedding IS NOT NULL
            ORDER BY al.embedding <=> :emb::vector
            LIMIT 8
        """),
        {"emb": vec_literal},
    ).fetchall()

    song_rows = db.execute(
        text("""
            SELECT s.id, s.title,
                   ar.id    AS artist_id,
                   ar.name  AS artist_name,
                   al.id    AS album_id,
                   al.title AS album_title,
                   al.cover_url,
                   1 - (s.embedding <=> :emb::vector) AS similarity
            FROM songs s
            JOIN artists ar ON ar.id = s.artist_id
            LEFT JOIN albums al ON al.id = s.album_id
            WHERE s.embedding IS NOT NULL
            ORDER BY s.embedding <=> :emb::vector
            LIMIT 8
        """),
        {"emb": vec_literal},
    ).fetchall()

    # Enrich any missing artist images inline
    artist_ids = [r.id for r in artist_rows]
    artists_db = (
        db.query(models.Artist).filter(models.Artist.id.in_(artist_ids)).all()
        if artist_ids else []
    )
    await _enrich_missing_images(db, artists_db, [])
    artist_images = {a.id: a.image_url for a in artists_db}

    return {
        "artists": [
            {
                "id": r.id,
                "name": r.name,
                "image_url": artist_images.get(r.id, r.image_url),
                "similarity": round(float(r.similarity), 3),
            }
            for r in artist_rows
        ],
        "albums": [
            {
                "id": r.id,
                "title": r.title,
                "cover_url": r.cover_url,
                "release_date": r.release_date,
                "artist": {"id": r.artist_id, "name": r.artist_name},
                "similarity": round(float(r.similarity), 3),
            }
            for r in album_rows
        ],
        "songs": [
            {
                "id": r.id,
                "title": r.title,
                "artist": {"id": r.artist_id, "name": r.artist_name},
                "album": {
                    "id": r.album_id,
                    "title": r.album_title,
                    "cover_url": r.cover_url,
                } if r.album_id else None,
                "similarity": round(float(r.similarity), 3),
            }
            for r in song_rows
        ],
    }


# ── Backfill endpoint ─────────────────────────────────────────────────────────

@router.post("/backfill")
async def backfill_embeddings(db: Session = Depends(get_db)):
    """
    Generate embeddings for all artists, albums, and songs that don't have one yet.
    Run this once after enabling the feature to seed the vector index.
    Processes items concurrently in batches of 10 to avoid rate-limiting.
    """
    from ..embeddings import (
        artist_text, album_text, song_text, get_embedding,
    )

    artists_todo = (
        db.query(models.Artist)
        .options(joinedload(models.Artist.genres))
        .filter(models.Artist.embedding.is_(None))
        .all()
    )
    albums_todo = (
        db.query(models.Album)
        .options(
            joinedload(models.Album.artist).joinedload(models.Artist.genres),
            joinedload(models.Album.genres),
            joinedload(models.Album.reviews),
        )
        .filter(models.Album.embedding.is_(None))
        .all()
    )
    songs_todo = (
        db.query(models.Song)
        .options(
            joinedload(models.Song.artist).joinedload(models.Artist.genres),
            joinedload(models.Song.album),
            joinedload(models.Song.reviews),
        )
        .filter(models.Song.embedding.is_(None))
        .all()
    )

    async def _embed_batch(items, text_fn) -> int:
        count = 0
        batch_size = 5
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            vectors = await asyncio.gather(
                *[get_embedding(text_fn(item)) for item in batch]
            )
            for item, vec in zip(batch, vectors):
                if vec is not None:
                    item.embedding = vec
                    count += 1
            db.commit()
            if i + batch_size < len(items):
                await asyncio.sleep(1.0)  # avoid OpenAI 429 rate limit
        return count

    artists_done = await _embed_batch(artists_todo, artist_text)
    albums_done  = await _embed_batch(albums_todo,  album_text)
    songs_done   = await _embed_batch(songs_todo,   song_text)

    return {
        "artists_embedded": artists_done,
        "albums_embedded":  albums_done,
        "songs_embedded":   songs_done,
        "total": artists_done + albums_done + songs_done,
    }
