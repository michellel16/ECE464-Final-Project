import asyncio

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import text, or_
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
    albums  = (
        db.query(models.Album)
        .join(models.Artist, models.Artist.id == models.Album.artist_id)
        .filter(or_(models.Album.title.ilike(like), models.Artist.name.ilike(like)))
        .limit(8).all()
    )
    songs   = (
        db.query(models.Song)
        .join(models.Artist, models.Artist.id == models.Song.artist_id)
        .filter(or_(models.Song.title.ilike(like), models.Artist.name.ilike(like)))
        .limit(8).all()
    )
    users   = db.query(models.User).filter(models.User.username.ilike(like)).limit(5).all()
    lists   = (
        db.query(models.List)
        .options(joinedload(models.List.user), joinedload(models.List.items))
        .filter(models.List.name.ilike(like), models.List.is_public == True)
        .limit(8).all()
    )

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
        "lists": [
            {
                "id": l.id, "name": l.name, "list_type": l.list_type,
                "item_count": len(l.items),
                "owner_username": l.user.username if l.user else None,
            }
            for l in lists
        ],
    }


# ── Genre keyword normalisation ───────────────────────────────────────────────
# Maps words that appear in Spotify genre slugs to the broad seeded genre name.
# "uk soul" → contains "soul" → R&B.  "bedroom pop" → contains "pop" → Pop.
_KEYWORD_TO_GENRE = {
    # R&B / Soul
    "soul": "R&B", "r&b": "R&B", "rhythm and blues": "R&B",
    "funk": "R&B", "motown": "R&B",
    # Hip-Hop
    "hip hop": "Hip-Hop", "hip-hop": "Hip-Hop",
    "rap": "Hip-Hop", "trap": "Hip-Hop", "drill": "Hip-Hop",
    "grime": "Hip-Hop",
    # Electronic
    "electronic": "Electronic", "edm": "Electronic", "synth": "Electronic",
    "dance": "Electronic", "house": "Electronic", "techno": "Electronic",
    "ambient": "Electronic",
    # Pop
    "pop": "Pop",
    # Rock / Alternative
    "rock": "Rock", "metal": "Rock", "punk": "Rock",
    "alternative": "Alternative", "grunge": "Alternative", "emo": "Alternative",
    # Indie
    "indie": "Indie", "lo-fi": "Indie", "lo fi": "Indie",
    # Folk
    "folk": "Folk", "country": "Folk", "americana": "Folk", "acoustic": "Folk",
    # Jazz
    "jazz": "Jazz",
    # Classical
    "classical": "Classical", "orchestra": "Classical", "symphon": "Classical",
}


def _genre_ids_for(anchor_genre_names: list[str], db: "Session") -> list[int]:
    """
    Given a list of (lowercased) Spotify genre slug names, return the IDs of
    all Genre rows in the DB that they map to — using both substring containment
    and the keyword map above.
    """
    all_genres = db.query(models.Genre).all()
    genre_id_by_name = {g.name.lower(): g.id for g in all_genres}
    matched: set[int] = set()

    for agn in anchor_genre_names:
        # 1. Direct substring containment
        for g in all_genres:
            gn = g.name.lower()
            if gn in agn or agn in gn:
                matched.add(g.id)
        # 2. Keyword map  ("soul" → "R&B", "pop" → "Pop", etc.)
        for keyword, seed_name in _KEYWORD_TO_GENRE.items():
            if keyword in agn:
                seed_id = genre_id_by_name.get(seed_name.lower())
                if seed_id:
                    matched.add(seed_id)

    return list(matched)


# ── Item-to-item similarity (no OpenAI — reads stored embeddings only) ────────

@router.get("/similar")
async def similar_items(
    item_type: str,
    item_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """
    Return items similar to the given artist/album/song.

    Four-level fallback for artists (no OpenAI calls):
      1. pgvector cosine similarity on stored embeddings
      2. Genre match — keyword map + substring (handles "uk soul" → R&B, etc.)
      3. Spotify Related Artists API — exact similarity graph, runs when genres fail
      4. Top-rated globally — guaranteed fallback
    Albums and songs use steps 1, 2, then top-rated.
    """
    if item_type == "artist":
        anchor = (
            db.query(models.Artist)
            .options(joinedload(models.Artist.genres))
            .filter(models.Artist.id == item_id)
            .first()
        )
        if anchor is None:
            return {"items": [], "label": None, "source": "none"}

        label = f"More like {anchor.name}"

        # ── 1. Embedding similarity ───────────────────────────────────────────
        if anchor.embedding is not None:
            vec = "[" + ",".join(f"{v:.8f}" for v in anchor.embedding) + "]"
            rows = db.execute(
                text("""
                    SELECT a.id, a.name, a.image_url,
                           1 - (a.embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM artists a
                    WHERE a.embedding IS NOT NULL AND a.id != :self_id
                    ORDER BY a.embedding <=> CAST(:emb AS vector)
                    LIMIT :lim
                """),
                {"emb": vec, "self_id": item_id, "lim": limit},
            ).fetchall()
            if rows:
                return {"items": [
                    {"item_type": "artist", "id": r.id, "name": r.name,
                     "image_url": r.image_url, "similarity": round(float(r.similarity), 3)}
                    for r in rows
                ], "label": label, "source": "embedding"}

        # ── 2. Genre match (substring + keyword map) ──────────────────────────
        anchor_genre_names = [g.name.lower() for g in anchor.genres]
        if anchor_genre_names:
            matched_ids = _genre_ids_for(anchor_genre_names, db)
            if matched_ids:
                rows = db.execute(
                    text("""
                        SELECT a.id, a.name, a.image_url, COUNT(*) AS shared
                        FROM artists a
                        JOIN artist_genre ag ON ag.artist_id = a.id
                        WHERE ag.genre_id = ANY(:gids) AND a.id != :self_id
                        GROUP BY a.id, a.name, a.image_url
                        ORDER BY shared DESC
                        LIMIT :lim
                    """),
                    {"gids": matched_ids, "self_id": item_id, "lim": limit},
                ).fetchall()
                if rows:
                    return {"items": [
                        {"item_type": "artist", "id": r.id, "name": r.name,
                         "image_url": r.image_url, "similarity": None}
                        for r in rows
                    ], "label": label, "source": "genre"}

        # ── 3. Spotify Related Artists ────────────────────────────────────────
        # Uses Spotify's own similarity graph — works even when genre tags are
        # empty or too niche. Only runs if Spotify client credentials are set.
        if anchor.spotify_id:
            try:
                token = await _get_client_token()
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"https://api.spotify.com/v1/artists/{anchor.spotify_id}/related-artists",
                        headers=_sp_headers(token),
                    )
                if resp.status_code == 200:
                    related_ids = [
                        a["id"] for a in resp.json().get("artists", [])[:20]
                        if a.get("id")
                    ]
                    if related_ids:
                        matched = (
                            db.query(models.Artist)
                            .filter(models.Artist.spotify_id.in_(related_ids))
                            .limit(limit)
                            .all()
                        )
                        if matched:
                            return {"items": [
                                {"item_type": "artist", "id": a.id, "name": a.name,
                                 "image_url": a.image_url, "similarity": None}
                                for a in matched
                            ], "label": label, "source": "spotify_related"}
            except Exception:
                pass  # Spotify not configured or rate-limited — fall through

        # ── 4. Top-rated globally ─────────────────────────────────────────────
        rows = db.execute(
            text("""
                SELECT a.id, a.name, a.image_url,
                       COUNT(DISTINCT r.id) AS review_count
                FROM artists a
                LEFT JOIN albums al ON al.artist_id = a.id
                LEFT JOIN reviews r ON r.album_id = al.id
                WHERE a.id != :self_id
                GROUP BY a.id, a.name, a.image_url
                ORDER BY review_count DESC
                LIMIT :lim
            """),
            {"self_id": item_id, "lim": limit},
        ).fetchall()
        return {"items": [
            {"item_type": "artist", "id": r.id, "name": r.name,
             "image_url": r.image_url, "similarity": None}
            for r in rows
        ], "label": "Popular on Tunelog", "source": "popular"}

    elif item_type == "album":
        anchor = (
            db.query(models.Album)
            .options(joinedload(models.Album.genres), joinedload(models.Album.artist))
            .filter(models.Album.id == item_id)
            .first()
        )
        if anchor is None:
            return {"items": [], "label": None, "source": "none"}

        label = f"Similar to {anchor.title}"

        # ── 1. Embedding similarity ───────────────────────────────────────────
        if anchor.embedding is not None:
            vec = "[" + ",".join(f"{v:.8f}" for v in anchor.embedding) + "]"
            rows = db.execute(
                text("""
                    SELECT al.id, al.title, al.cover_url, al.release_date,
                           ar.id AS artist_id, ar.name AS artist_name,
                           1 - (al.embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM albums al
                    JOIN artists ar ON ar.id = al.artist_id
                    WHERE al.embedding IS NOT NULL AND al.id != :self_id
                    ORDER BY al.embedding <=> CAST(:emb AS vector)
                    LIMIT :lim
                """),
                {"emb": vec, "self_id": item_id, "lim": limit},
            ).fetchall()
            if rows:
                return {"items": [
                    {"item_type": "album", "id": r.id, "title": r.title,
                     "cover_url": r.cover_url, "release_date": r.release_date,
                     "artist": {"id": r.artist_id, "name": r.artist_name},
                     "similarity": round(float(r.similarity), 3)}
                    for r in rows
                ], "label": label, "source": "embedding"}

        # ── 2. Genre match (substring + keyword map) ──────────────────────────
        anchor_genre_names = [g.name.lower() for g in anchor.genres]
        if anchor_genre_names:
            matched_ids = _genre_ids_for(anchor_genre_names, db)
            if matched_ids:
                rows = db.execute(
                    text("""
                        SELECT al.id, al.title, al.cover_url, al.release_date,
                               ar.id AS artist_id, ar.name AS artist_name,
                               COUNT(*) AS shared
                        FROM albums al
                        JOIN artists ar ON ar.id = al.artist_id
                        JOIN album_genre ag ON ag.album_id = al.id
                        WHERE ag.genre_id = ANY(:gids) AND al.id != :self_id
                        GROUP BY al.id, al.title, al.cover_url, al.release_date, ar.id, ar.name
                        ORDER BY shared DESC
                        LIMIT :lim
                    """),
                    {"gids": matched_ids, "self_id": item_id, "lim": limit},
                ).fetchall()
                if rows:
                    return {"items": [
                        {"item_type": "album", "id": r.id, "title": r.title,
                         "cover_url": r.cover_url, "release_date": r.release_date,
                         "artist": {"id": r.artist_id, "name": r.artist_name},
                         "similarity": None}
                        for r in rows
                    ], "label": label, "source": "genre"}

        # ── 3. Top-rated globally ─────────────────────────────────────────────
        rows = db.execute(
            text("""
                SELECT al.id, al.title, al.cover_url, al.release_date,
                       ar.id AS artist_id, ar.name AS artist_name,
                       COALESCE(AVG(r.rating), 0) AS avg_rating
                FROM albums al
                JOIN artists ar ON ar.id = al.artist_id
                LEFT JOIN reviews r ON r.album_id = al.id
                WHERE al.id != :self_id
                GROUP BY al.id, al.title, al.cover_url, al.release_date, ar.id, ar.name
                ORDER BY avg_rating DESC
                LIMIT :lim
            """),
            {"self_id": item_id, "lim": limit},
        ).fetchall()
        return {"items": [
            {"item_type": "album", "id": r.id, "title": r.title,
             "cover_url": r.cover_url, "release_date": r.release_date,
             "artist": {"id": r.artist_id, "name": r.artist_name},
             "similarity": None}
            for r in rows
        ], "label": "Popular on Tunelog", "source": "popular"}

    elif item_type == "song":
        anchor = (
            db.query(models.Song)
            .options(
                joinedload(models.Song.artist).joinedload(models.Artist.genres),
                joinedload(models.Song.album),
            )
            .filter(models.Song.id == item_id)
            .first()
        )
        if anchor is None:
            return {"items": [], "label": None, "source": "none"}

        label = f"Similar to {anchor.title}"

        # ── 1. Embedding similarity ───────────────────────────────────────────
        if anchor.embedding is not None:
            vec = "[" + ",".join(f"{v:.8f}" for v in anchor.embedding) + "]"
            rows = db.execute(
                text("""
                    SELECT s.id, s.title,
                           ar.id AS artist_id, ar.name AS artist_name,
                           al.id AS album_id, al.title AS album_title, al.cover_url,
                           1 - (s.embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM songs s
                    JOIN artists ar ON ar.id = s.artist_id
                    LEFT JOIN albums al ON al.id = s.album_id
                    WHERE s.embedding IS NOT NULL AND s.id != :self_id
                    ORDER BY s.embedding <=> CAST(:emb AS vector)
                    LIMIT :lim
                """),
                {"emb": vec, "self_id": item_id, "lim": limit},
            ).fetchall()
            if rows:
                return {"items": [
                    {"item_type": "song", "id": r.id, "title": r.title,
                     "artist": {"id": r.artist_id, "name": r.artist_name},
                     "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
                     "similarity": round(float(r.similarity), 3)}
                    for r in rows
                ], "label": label, "source": "embedding"}

        # ── 2. Other songs by same artist ─────────────────────────────────────
        rows = db.execute(
            text("""
                SELECT s.id, s.title,
                       ar.id AS artist_id, ar.name AS artist_name,
                       al.id AS album_id, al.title AS album_title, al.cover_url
                FROM songs s
                JOIN artists ar ON ar.id = s.artist_id
                LEFT JOIN albums al ON al.id = s.album_id
                WHERE s.artist_id = :artist_id AND s.id != :self_id
                LIMIT :lim
            """),
            {"artist_id": anchor.artist_id, "self_id": item_id, "lim": limit},
        ).fetchall()
        if rows:
            artist_name = anchor.artist.name if anchor.artist else "this artist"
            return {"items": [
                {"item_type": "song", "id": r.id, "title": r.title,
                 "artist": {"id": r.artist_id, "name": r.artist_name},
                 "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
                 "similarity": None}
                for r in rows
            ], "label": f"More from {artist_name}", "source": "artist"}

        # ── 3. Top-rated globally ─────────────────────────────────────────────
        rows = db.execute(
            text("""
                SELECT s.id, s.title,
                       ar.id AS artist_id, ar.name AS artist_name,
                       al.id AS album_id, al.title AS album_title, al.cover_url
                FROM songs s
                JOIN artists ar ON ar.id = s.artist_id
                LEFT JOIN albums al ON al.id = s.album_id
                LEFT JOIN reviews r ON r.song_id = s.id
                WHERE s.id != :self_id
                GROUP BY s.id, s.title, ar.id, ar.name, al.id, al.title, al.cover_url
                ORDER BY COALESCE(AVG(r.rating), 0) DESC
                LIMIT :lim
            """),
            {"self_id": item_id, "lim": limit},
        ).fetchall()
        return {"items": [
            {"item_type": "song", "id": r.id, "title": r.title,
             "artist": {"id": r.artist_id, "name": r.artist_name},
             "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
             "similarity": None}
            for r in rows
        ], "label": "Popular on Tunelog", "source": "popular"}


# ── Semantic (vibe) search ────────────────────────────────────────────────────

@router.get("/semantic")
async def semantic_search(q: str):
    """
    Embed the query with OpenAI text-embedding-3-small then rank artists,
    albums, and songs by cosine similarity against stored pgvector embeddings.

    DB session is intentionally opened AFTER get_embedding() so a long
    OpenAI wait (rate-limit retry) never holds a pool connection.
    """
    from ..embeddings import get_embedding
    from ..database import SessionLocal

    # Step 1: get embedding — no DB connection held while OpenAI may be slow.
    vec = await get_embedding(q)
    if vec is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable — check OPENAI_API_KEY",
        )

    vec_literal = "[" + ",".join(f"{v:.8f}" for v in vec) + "]"

    # Step 2: all DB work happens in a short window after embedding is ready.
    db = SessionLocal()
    try:
        artist_rows = db.execute(
            text("""
                SELECT id, name, image_url,
                       1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                FROM artists
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT 5
            """),
            {"emb": vec_literal},
        ).fetchall()

        album_rows = db.execute(
            text("""
                SELECT al.id, al.title, al.cover_url, al.release_date,
                       ar.id   AS artist_id,
                       ar.name AS artist_name,
                       1 - (al.embedding <=> CAST(:emb AS vector)) AS similarity
                FROM albums al
                JOIN artists ar ON ar.id = al.artist_id
                WHERE al.embedding IS NOT NULL
                ORDER BY al.embedding <=> CAST(:emb AS vector)
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
                       1 - (s.embedding <=> CAST(:emb AS vector)) AS similarity
                FROM songs s
                JOIN artists ar ON ar.id = s.artist_id
                LEFT JOIN albums al ON al.id = s.album_id
                WHERE s.embedding IS NOT NULL
                ORDER BY s.embedding <=> CAST(:emb AS vector)
                LIMIT 8
            """),
            {"emb": vec_literal},
        ).fetchall()

    finally:
        db.close()

    return {
        "artists": [
            {
                "id": r.id,
                "name": r.name,
                "image_url": r.image_url,
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


# ── Embedding status ─────────────────────────────────────────────────────────

@router.get("/backfill/status")
def backfill_status(db: Session = Depends(get_db)):
    def counts(model, col):
        total     = db.query(model).count()
        embedded  = db.query(model).filter(col.isnot(None)).count()
        return {"embedded": embedded, "total": total, "remaining": total - embedded}

    artists = counts(models.Artist, models.Artist.embedding)
    albums  = counts(models.Album,  models.Album.embedding)
    songs   = counts(models.Song,   models.Song.embedding)

    remaining = artists["remaining"] + albums["remaining"] + songs["remaining"]
    est_seconds = (remaining // 5) * 1 + (remaining * 0.3)

    return {
        "artists": artists,
        "albums":  albums,
        "songs":   songs,
        "total_remaining": remaining,
        "estimated_seconds": round(est_seconds),
    }


# ── Backfill endpoint ─────────────────────────────────────────────────────────

async def _run_backfill():
    """
    Background task — opens its own session so the HTTP response returns immediately.
    Processes items in small pages so it never loads thousands of rows at once.
    Stops immediately if OpenAI is not configured or all embeddings fail.
    """
    import logging
    from ..embeddings import artist_text, album_text, song_text, get_embedding, OPENAI_API_KEY
    from ..database import SessionLocal

    log = logging.getLogger(__name__)

    if not OPENAI_API_KEY:
        log.error("Backfill aborted: OPENAI_API_KEY is not set")
        return

    PAGE = 5

    steps = [
        (models.Artist, models.Artist.embedding,
         lambda db: db.query(models.Artist).options(joinedload(models.Artist.genres)),
         artist_text),
        (models.Album, models.Album.embedding,
         lambda db: db.query(models.Album).options(
             joinedload(models.Album.artist).joinedload(models.Artist.genres),
             joinedload(models.Album.genres),
             joinedload(models.Album.reviews),
         ),
         album_text),
        (models.Song, models.Song.embedding,
         lambda db: db.query(models.Song).options(
             joinedload(models.Song.artist).joinedload(models.Artist.genres),
             joinedload(models.Song.album),
             joinedload(models.Song.reviews),
         ),
         song_text),
    ]

    for _model, emb_col, base_query, text_fn in steps:
        offset = 0
        consecutive_failures = 0
        while True:
            db = SessionLocal()
            try:
                items = (
                    base_query(db)
                    .filter(emb_col.is_(None))
                    .offset(offset)
                    .limit(PAGE)
                    .all()
                )
                if not items:
                    break

                vectors = await asyncio.gather(
                    *[get_embedding(text_fn(item)) for item in items]
                )

                saved = 0
                for item, vec in zip(items, vectors):
                    if vec is None:
                        continue
                    item.embedding = vec
                    try:
                        db.commit()
                        saved += 1
                    except Exception as write_exc:
                        log.warning("Backfill write failed for id=%s: %s — retrying with fresh session", item.id, write_exc)
                        db.close()
                        db = SessionLocal()
                        # Re-fetch and retry once with a fresh connection
                        try:
                            fresh = db.query(_model).filter(_model.id == item.id).first()
                            if fresh:
                                fresh.embedding = vec
                                db.commit()
                                saved += 1
                        except Exception as retry_exc:
                            log.error("Backfill retry failed for id=%s: %s", item.id, retry_exc)

                if saved == 0:
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        log.error("Backfill: no embeddings succeeded for 3 consecutive pages — aborting (check OPENAI_API_KEY and rate limits)")
                        return
                else:
                    consecutive_failures = 0

                offset += saved
            except Exception as exc:
                log.warning("Backfill page fetch failed: %s — retrying after 5s", exc)
                await asyncio.sleep(5.0)
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    log.error("Backfill: too many consecutive failures — aborting")
                    return
                continue
            finally:
                db.close()

            await asyncio.sleep(1.0)


@router.post("/backfill")
async def backfill_embeddings(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_backfill)
    return {"status": "started — poll GET /api/search/backfill/status to track progress"}
