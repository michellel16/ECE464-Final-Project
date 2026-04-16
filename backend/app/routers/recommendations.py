"""
Vector-based personalized music recommendations.

Algorithm
---------
1. Collect embeddings of every album/song the user has interacted with
   (reviewed OR set a listen/favorite/want status on).
2. Build a weighted taste-centroid:
     - Reviewed item  →  weight = rating / 5.0  (range 0.1 – 1.0)
     - Favorited       →  weight = 0.9
     - Listened        →  weight = 0.6
3. L2-normalize the centroid and run a pgvector ANN query to rank every
   *unseen* album and song by cosine similarity.
4. Fallback: if the user has fewer than 2 items with embeddings, return the
   community's top-rated albums/songs instead (useful for new accounts).
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text, func
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

_MIN_PROFILE_SIZE = 2   # minimum embedded items needed for vector recs


# ── Vector helpers ────────────────────────────────────────────────────────────

def _weighted_centroid(
    embeddings: list[list[float]],
    weights: list[float],
) -> Optional[list[float]]:
    """Return a weight-averaged, L2-normalized centroid, or None if inputs are empty."""
    if not embeddings:
        return None
    dim = len(embeddings[0])
    total = sum(weights)
    if total == 0:
        return None
    centroid = [0.0] * dim
    for vec, w in zip(embeddings, weights):
        for i in range(dim):
            centroid[i] += vec[i] * (w / total)
    norm = math.sqrt(sum(x * x for x in centroid))
    if norm > 0:
        centroid = [x / norm for x in centroid]
    return centroid


def _vec_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


# ── Main recommendation endpoint ──────────────────────────────────────────────

@router.get("/me")
def my_recommendations(
    album_limit: int = 6,
    song_limit: int = 8,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id

    # ── Step 1: collect seen IDs ──────────────────────────────────────────────
    seen_album_ids: set[int] = set()
    seen_song_ids: set[int] = set()

    # From reviews
    for r in db.query(models.Review).filter_by(user_id=uid).all():
        if r.album_id:
            seen_album_ids.add(r.album_id)
        if r.song_id:
            seen_song_ids.add(r.song_id)

    # From album statuses
    for s in db.query(models.UserAlbumStatus).filter_by(user_id=uid).all():
        seen_album_ids.add(s.album_id)

    # From song statuses
    for s in db.query(models.UserSongStatus).filter_by(user_id=uid).all():
        seen_song_ids.add(s.song_id)

    # Also exclude songs belonging to seen albums
    if seen_album_ids:
        for row in (
            db.query(models.Song.id)
            .filter(models.Song.album_id.in_(seen_album_ids))
            .all()
        ):
            seen_song_ids.add(row[0])

    # From lists
    list_ids = [r[0] for r in db.query(models.List.id).filter_by(user_id=uid).all()]
    if list_ids:
        for li in (
            db.query(models.ListItem)
            .filter(models.ListItem.list_id.in_(list_ids))
            .all()
        ):
            if li.album_id:
                seen_album_ids.add(li.album_id)
            if li.song_id:
                seen_song_ids.add(li.song_id)

    # ── Step 2: build taste-profile centroid ──────────────────────────────────
    profile_vecs: list[list[float]] = []
    profile_weights: list[float] = []

    # From reviews — use the album OR song embedding, whichever exists
    reviews = (
        db.query(models.Review)
        .options(
            joinedload(models.Review.album),
            joinedload(models.Review.song),
        )
        .filter_by(user_id=uid)
        .all()
    )
    for rev in reviews:
        target = rev.album if rev.album_id else rev.song
        if target is not None and target.embedding is not None:
            emb = list(target.embedding)  # pgvector → Python list
            profile_vecs.append(emb)
            profile_weights.append(rev.rating / 5.0)

    # From album statuses (favorites get higher weight)
    album_statuses = (
        db.query(models.UserAlbumStatus)
        .options(joinedload(models.UserAlbumStatus.album))
        .filter_by(user_id=uid)
        .all()
    )
    for st in album_statuses:
        if st.album and st.album.embedding is not None:
            # Don't double-count if we already have a review for this album
            already_reviewed = any(
                r.album_id == st.album_id for r in reviews
            )
            if not already_reviewed:
                emb = list(st.album.embedding)
                w = 0.9 if st.status == "favorites" else 0.6
                profile_vecs.append(emb)
                profile_weights.append(w)

    # From song statuses
    song_statuses = (
        db.query(models.UserSongStatus)
        .options(joinedload(models.UserSongStatus.song))
        .filter_by(user_id=uid)
        .all()
    )
    for st in song_statuses:
        if st.song and st.song.embedding is not None:
            already_reviewed = any(
                r.song_id == st.song_id for r in reviews
            )
            if not already_reviewed:
                emb = list(st.song.embedding)
                w = 0.9 if st.status == "favorites" else 0.6
                profile_vecs.append(emb)
                profile_weights.append(w)

    profile_size = len(profile_vecs)

    # ── Step 3: pick strategy ─────────────────────────────────────────────────
    if profile_size >= _MIN_PROFILE_SIZE:
        centroid = _weighted_centroid(profile_vecs, profile_weights)
        albums, songs = _vector_recs(
            db, centroid, seen_album_ids, seen_song_ids,
            album_limit, song_limit,
        )
        source = "embedding"
    else:
        albums, songs = _fallback_recs(
            db, seen_album_ids, seen_song_ids,
            album_limit, song_limit,
        )
        source = "fallback"

    return {
        "albums": albums,
        "songs": songs,
        "source": source,
        "profile_size": profile_size,
    }


# ── Vector strategy ───────────────────────────────────────────────────────────

def _vector_recs(
    db: Session,
    centroid: list[float],
    seen_album_ids: set[int],
    seen_song_ids: set[int],
    album_limit: int,
    song_limit: int,
) -> tuple[list[dict], list[dict]]:
    vec = _vec_literal(centroid)

    # Exclude clause: pgvector works fastest with NOT IN on small sets
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
              AND al.id != ALL(:excl)
            ORDER BY al.embedding <=> :emb::vector
            LIMIT :lim
        """),
        {"emb": vec, "excl": excl_albums, "lim": album_limit},
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
              AND s.id != ALL(:excl)
            ORDER BY s.embedding <=> :emb::vector
            LIMIT :lim
        """),
        {"emb": vec, "excl": excl_songs, "lim": song_limit},
    ).fetchall()

    albums = [
        {
            "id": r.id,
            "title": r.title,
            "cover_url": r.cover_url,
            "release_date": r.release_date,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "similarity": round(float(r.similarity), 3),
            "reason": _similarity_reason(float(r.similarity)),
        }
        for r in album_rows
    ]
    songs = [
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
            "reason": _similarity_reason(float(r.similarity)),
        }
        for r in song_rows
    ]
    return albums, songs


def _similarity_reason(sim: float) -> str:
    if sim >= 0.92:
        return "Matches your taste"
    if sim >= 0.85:
        return "Very similar to what you love"
    if sim >= 0.75:
        return "You might enjoy this"
    return "Worth discovering"


# ── Fallback strategy (community top-rated) ───────────────────────────────────

def _fallback_recs(
    db: Session,
    seen_album_ids: set[int],
    seen_song_ids: set[int],
    album_limit: int,
    song_limit: int,
) -> tuple[list[dict], list[dict]]:
    """Return globally top-rated albums and songs the user hasn't seen."""
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
            WHERE al.id != ALL(:excl)
            GROUP BY al.id, ar.id, ar.name
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT :lim
        """),
        {"excl": excl_albums, "lim": album_limit},
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
            WHERE s.id != ALL(:excl)
            GROUP BY s.id, ar.id, ar.name, al.id, al.title, al.cover_url
            ORDER BY avg_rating DESC
            LIMIT :lim
        """),
        {"excl": excl_songs, "lim": song_limit},
    ).fetchall()

    albums = [
        {
            "id": r.id,
            "title": r.title,
            "cover_url": r.cover_url,
            "release_date": r.release_date,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "similarity": None,
            "reason": "Highly rated on Tunelog",
        }
        for r in album_rows
    ]
    songs = [
        {
            "id": r.id,
            "title": r.title,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "album": {
                "id": r.album_id,
                "title": r.album_title,
                "cover_url": r.cover_url,
            } if r.album_id else None,
            "similarity": None,
            "reason": "Popular on Tunelog",
        }
        for r in song_rows
    ]
    return albums, songs
