"""
Vector-based personalized music recommendations.

Algorithm
---------
1. Cached taste embedding (zero-latency, no network): if the user's stored
   taste embedding matches the current profile fingerprint, run ANN immediately.

2. Weighted centroid of stored item embeddings: average the pgvector embeddings
   of items the user has rated/favourited, then run ANN. No external calls.

3. Community top-rated: fallback when the user has < 2 interactions.

When the taste embedding is stale or missing, a background task is enqueued to
call OpenAI and update the cache — so the next request can use path 1. This
keeps OpenAI rate limits entirely out of the hot request path.
"""
import hashlib
import logging
import math
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db, SessionLocal
from ..auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

_MIN_PROFILE_SIZE = 2


# ── Taste-profile helpers ──────────────────────────────────────────────────────

def _profile_fingerprint(reviews, album_statuses, song_statuses) -> str:
    parts = (
        [f"r{r.id}:{r.rating:.1f}" for r in sorted(reviews, key=lambda x: x.id)]
        + [f"as{s.album_id}:{s.status}" for s in sorted(album_statuses, key=lambda x: x.album_id)]
        + [f"ss{s.song_id}:{s.status}" for s in sorted(song_statuses, key=lambda x: x.song_id)]
    )
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:64]


def _build_taste_text(reviews, album_statuses, song_statuses) -> str:
    parts = ["Music taste profile:"]

    for rev in sorted(reviews, key=lambda r: -(r.rating or 0))[:12]:
        if rev.album and getattr(rev.album, "artist", None):
            parts.append(f"Rated {rev.album.title} by {rev.album.artist.name} {rev.rating}/5")
        elif rev.song and getattr(rev.song, "artist", None):
            parts.append(f"Rated {rev.song.title} by {rev.song.artist.name} {rev.rating}/5")

    for st in album_statuses:
        if st.status == "favorites" and st.album:
            a = getattr(st.album, "artist", None)
            parts.append(f"Favorited album {st.album.title}" + (f" by {a.name}" if a else ""))

    for st in song_statuses:
        if st.status == "favorites" and st.song:
            a = getattr(st.song, "artist", None)
            parts.append(f"Favorited song {st.song.title}" + (f" by {a.name}" if a else ""))

    genre_counts: dict[str, int] = {}
    for rev in reviews:
        if (rev.rating or 0) >= 4.0:
            target = rev.album or rev.song
            if target:
                genres = list(getattr(target, "genres", None) or [])
                if not genres and getattr(target, "artist", None):
                    genres = list(getattr(target.artist, "genres", None) or [])
                for g in genres:
                    genre_counts[g.name] = genre_counts.get(g.name, 0) + 1
    top_genres = sorted(genre_counts, key=lambda x: -genre_counts[x])[:5]
    if top_genres:
        parts.append(f"Preferred genres: {', '.join(top_genres)}")

    return ". ".join(parts)


def _get_cached_embedding(user: models.User, fingerprint: str) -> Optional[list[float]]:
    """Return the stored taste embedding only if the profile fingerprint still matches."""
    if user.taste_profile_hash == fingerprint and user.taste_embedding is not None:
        return list(user.taste_embedding)
    return None


async def _refresh_taste_embedding_bg(user_id: int, taste_text: str, fingerprint: str) -> None:
    """Background task: call OpenAI and persist the result — never blocks the request."""
    from ..embeddings import get_embedding

    vec = await get_embedding(taste_text)
    if vec is None:
        return

    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(id=user_id).first()
        if user:
            user.taste_embedding = vec
            user.taste_profile_hash = fingerprint
            db.commit()
    except Exception as exc:
        logger.error("Background taste embedding update failed for user %d: %s", user_id, exc)
    finally:
        db.close()


# ── Vector helpers ─────────────────────────────────────────────────────────────

def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


def _weighted_centroid(embeddings: list, weights: list) -> Optional[list[float]]:
    if not embeddings:
        return None
    total = sum(weights)
    if total == 0:
        return None
    dim = len(embeddings[0])
    centroid = [0.0] * dim
    for vec, w in zip(embeddings, weights):
        for i in range(dim):
            centroid[i] += vec[i] * (w / total)
    norm = math.sqrt(sum(x * x for x in centroid))
    if norm > 0:
        centroid = [x / norm for x in centroid]
    return centroid


def _similarity_reason(sim: float) -> str:
    if sim >= 0.92:
        return "Matches your taste"
    if sim >= 0.85:
        return "Very similar to what you love"
    if sim >= 0.75:
        return "You might enjoy this"
    return "Worth discovering"


# ── Query strategies ───────────────────────────────────────────────────────────

def _vector_recs(
    db: Session,
    centroid: list[float],
    seen_album_ids: set[int],
    seen_song_ids: set[int],
    album_limit: int,
    song_limit: int,
) -> tuple[list[dict], list[dict]]:
    vec = _vec_literal(centroid)
    excl_albums = list(seen_album_ids) or [-1]
    excl_songs  = list(seen_song_ids)  or [-1]

    album_rows = db.execute(
        text("""
            SELECT al.id, al.title, al.cover_url, al.release_date,
                   ar.id   AS artist_id,
                   ar.name AS artist_name,
                   1 - (al.embedding <=> :emb::vector) AS similarity
            FROM albums al
            JOIN artists ar ON ar.id = al.artist_id
            WHERE al.embedding IS NOT NULL
              AND al.id != ALL(:excl_albums)
            ORDER BY al.embedding <=> :emb::vector
            LIMIT :lim
        """),
        {"emb": vec, "excl_albums": excl_albums, "lim": album_limit},
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
              AND s.id != ALL(:excl_songs)
            ORDER BY s.embedding <=> :emb::vector
            LIMIT :lim
        """),
        {"emb": vec, "excl_songs": excl_songs, "lim": song_limit},
    ).fetchall()

    albums = [
        {
            "id": r.id, "title": r.title, "cover_url": r.cover_url,
            "release_date": r.release_date,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "similarity": round(float(r.similarity), 3),
            "reason": _similarity_reason(float(r.similarity)),
        }
        for r in album_rows
    ]
    songs = [
        {
            "id": r.id, "title": r.title,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
            "similarity": round(float(r.similarity), 3),
            "reason": _similarity_reason(float(r.similarity)),
        }
        for r in song_rows
    ]
    return albums, songs


def _fallback_recs(
    db: Session,
    seen_album_ids: set[int],
    seen_song_ids: set[int],
    album_limit: int,
    song_limit: int,
) -> tuple[list[dict], list[dict]]:
    excl_albums = list(seen_album_ids) or [-1]
    excl_songs  = list(seen_song_ids)  or [-1]

    album_rows = db.execute(
        text("""
            SELECT al.id, al.title, al.cover_url, al.release_date,
                   ar.id AS artist_id, ar.name AS artist_name,
                   COALESCE(AVG(r.rating), 0) AS avg_rating,
                   COUNT(r.id) AS review_count
            FROM albums al
            JOIN artists ar ON ar.id = al.artist_id
            LEFT JOIN reviews r ON r.album_id = al.id
            WHERE al.id != ALL(:excl_albums)
            GROUP BY al.id, ar.id, ar.name
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT :lim
        """),
        {"excl_albums": excl_albums, "lim": album_limit},
    ).fetchall()

    song_rows = db.execute(
        text("""
            SELECT s.id, s.title,
                   ar.id AS artist_id, ar.name AS artist_name,
                   al.id AS album_id, al.title AS album_title, al.cover_url,
                   COALESCE(AVG(r.rating), 0) AS avg_rating
            FROM songs s
            JOIN artists ar ON ar.id = s.artist_id
            LEFT JOIN albums al ON al.id = s.album_id
            LEFT JOIN reviews r ON r.song_id = s.id
            WHERE s.id != ALL(:excl_songs)
            GROUP BY s.id, ar.id, ar.name, al.id, al.title, al.cover_url
            ORDER BY avg_rating DESC
            LIMIT :lim
        """),
        {"excl_songs": excl_songs, "lim": song_limit},
    ).fetchall()

    albums = [
        {
            "id": r.id, "title": r.title, "cover_url": r.cover_url,
            "release_date": r.release_date,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "similarity": None, "reason": "Highly rated on Tunelog",
        }
        for r in album_rows
    ]
    songs = [
        {
            "id": r.id, "title": r.title,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
            "similarity": None, "reason": "Popular on Tunelog",
        }
        for r in song_rows
    ]
    return albums, songs


# ── Main endpoint ──────────────────────────────────────────────────────────────

@router.get("/me")
async def my_recommendations(
    background_tasks: BackgroundTasks,
    album_limit: int = 6,
    song_limit: int = 8,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id

    reviews = (
        db.query(models.Review)
        .options(
            joinedload(models.Review.album)
                .joinedload(models.Album.artist)
                .joinedload(models.Artist.genres),
            joinedload(models.Review.album).joinedload(models.Album.genres),
            joinedload(models.Review.song)
                .joinedload(models.Song.artist)
                .joinedload(models.Artist.genres),
        )
        .filter_by(user_id=uid)
        .all()
    )

    album_statuses = (
        db.query(models.UserAlbumStatus)
        .options(
            joinedload(models.UserAlbumStatus.album).joinedload(models.Album.artist),
        )
        .filter_by(user_id=uid)
        .all()
    )

    song_statuses = (
        db.query(models.UserSongStatus)
        .options(
            joinedload(models.UserSongStatus.song).joinedload(models.Song.artist),
        )
        .filter_by(user_id=uid)
        .all()
    )

    seen_album_ids: set[int] = set()
    seen_song_ids: set[int] = set()

    for r in reviews:
        if r.album_id:
            seen_album_ids.add(r.album_id)
        if r.song_id:
            seen_song_ids.add(r.song_id)

    for s in album_statuses:
        seen_album_ids.add(s.album_id)

    for s in song_statuses:
        seen_song_ids.add(s.song_id)

    if seen_album_ids:
        for row in db.query(models.Song.id).filter(models.Song.album_id.in_(seen_album_ids)).all():
            seen_song_ids.add(row[0])

    list_ids = [r[0] for r in db.query(models.List.id).filter_by(user_id=uid).all()]
    if list_ids:
        for li in db.query(models.ListItem).filter(models.ListItem.list_id.in_(list_ids)).all():
            if li.album_id:
                seen_album_ids.add(li.album_id)
            if li.song_id:
                seen_song_ids.add(li.song_id)

    profile_size = len(reviews) + len(album_statuses) + len(song_statuses)

    if profile_size >= _MIN_PROFILE_SIZE:
        fp = _profile_fingerprint(reviews, album_statuses, song_statuses)

        # 1. Cached taste embedding — serve instantly, zero network calls
        taste_vec = _get_cached_embedding(current_user, fp)

        # If stale or missing, enqueue a background refresh for the next request
        if taste_vec is None:
            taste_text = _build_taste_text(reviews, album_statuses, song_statuses)
            if taste_text != "Music taste profile:":
                background_tasks.add_task(_refresh_taste_embedding_bg, uid, taste_text, fp)

        if taste_vec:
            albums, songs = _vector_recs(
                db, taste_vec,
                seen_album_ids, seen_song_ids,
                album_limit, song_limit,
            )
            return {"albums": albums, "songs": songs, "source": "embedding", "profile_size": profile_size}

        # 2. Weighted centroid of stored item embeddings — personalized, no OpenAI needed
        profile_vecs: list[list[float]] = []
        profile_weights: list[float] = []
        for rev in reviews:
            target = rev.album if rev.album_id else rev.song
            if target and target.embedding is not None:
                profile_vecs.append(list(target.embedding))
                profile_weights.append(rev.rating / 5.0)
        for st in album_statuses:
            if st.album and st.album.embedding is not None:
                if not any(r.album_id == st.album_id for r in reviews):
                    w = 0.9 if st.status == "favorites" else 0.6
                    profile_vecs.append(list(st.album.embedding))
                    profile_weights.append(w)
        for st in song_statuses:
            if st.song and st.song.embedding is not None:
                if not any(r.song_id == st.song_id for r in reviews):
                    w = 0.9 if st.status == "favorites" else 0.6
                    profile_vecs.append(list(st.song.embedding))
                    profile_weights.append(w)

        if len(profile_vecs) >= _MIN_PROFILE_SIZE:
            centroid = _weighted_centroid(profile_vecs, profile_weights)
            if centroid:
                albums, songs = _vector_recs(
                    db, centroid,
                    seen_album_ids, seen_song_ids,
                    album_limit, song_limit,
                )
                return {"albums": albums, "songs": songs, "source": "centroid", "profile_size": profile_size}

    # 3. Community top-rated fallback
    albums, songs = _fallback_recs(
        db, seen_album_ids, seen_song_ids, album_limit, song_limit
    )
    return {"albums": albums, "songs": songs, "source": "fallback", "profile_size": profile_size}
