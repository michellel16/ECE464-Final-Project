"""
Vector-based personalized music recommendations.

Algorithm — four-path cascade
------------------------------
1. Cached taste embedding  (zero-latency, no network call):
   If the user's stored `taste_embedding` matches the current profile
   fingerprint (sha-256 of all interactions), we run an ANN query against
   the pgvector HNSW index immediately.  When the profile changes, a
   background task regenerates the embedding so the *next* request lands
   here again.

2. Weighted centroid of stored item embeddings  (no external calls):
   Compute a weighted average of the pgvector vectors already stored on the
   albums/songs the user has interacted with.  Weight = rating / 5 for
   reviews; 0.9 for favorited, 0.6 for listened statuses.  The centroid is
   L2-normalised so cosine distance queries work correctly.

3. Per-interest preference clusters  (background-fetched, cache-only hot path):
   Each stated genre/mood/free-text preference is embedded separately.
   Results from every cluster are round-robin merged for diversity.
   The preference embeddings are fetched in a background task and cached
   in-process; the hot path reads from the cache without any network call.

4. Community top-rated  (no embeddings needed):
   Fallback for brand-new users with no listening history and no cached
   preference embeddings yet.

When paths 1/2 have preference vectors available they are combined with the
listening-history vector via round-robin merge so the result reflects both
what the user has *actually* listened to and what they *say* they like.

pgvector notes
--------------
- Operator `<=>` is cosine distance (0 = identical, 2 = opposite).
- Similarity = 1 − cosine_distance, so 1.0 is a perfect match.
- The HNSW index on each embeddings column makes ANN queries O(log n).
- A minimum similarity threshold of MIN_SIMILARITY filters out noise while
  the fallback path guarantees the endpoint always returns results.
"""
import hashlib
import json
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

# Cosine-similarity floor: items with similarity below this are too distant
# from the user's taste vector to surface.  The fallback path ignores this
# threshold since it doesn't use embeddings.
MIN_SIMILARITY = 0.45

# In-process cache: embedding text → vector (stable across requests, cleared on restart)
_pref_embedding_cache: dict[str, list[float]] = {}

# In-flight guards: prevent queuing duplicate background tasks for the same key.
_pref_bg_inflight: set[str] = set()
_taste_bg_inflight: set[int] = set()


async def _fetch_pref_embeddings_bg(texts: list[str]) -> None:
    """Background: fetch missing preference embeddings one at a time."""
    from ..embeddings import get_embedding, is_embedding_cooling_down
    _pref_bg_inflight.update(texts)
    try:
        for t in texts:
            if t not in _pref_embedding_cache and not is_embedding_cooling_down(t):
                vec = await get_embedding(t)
                if vec is not None:
                    _pref_embedding_cache[t] = vec
    finally:
        _pref_bg_inflight.difference_update(texts)


# ── Taste-profile helpers ──────────────────────────────────────────────────────

def _profile_fingerprint(reviews, album_statuses, song_statuses, preferences: dict | None = None) -> str:
    parts = (
        [f"r{r.id}:{r.rating:.1f}" for r in sorted(reviews, key=lambda x: x.id)]
        + [f"as{s.album_id}:{s.status}" for s in sorted(album_statuses, key=lambda x: x.album_id)]
        + [f"ss{s.song_id}:{s.status}" for s in sorted(song_statuses, key=lambda x: x.song_id)]
    )
    if preferences:
        parts.append(f"prefs:{json.dumps(preferences, sort_keys=True)}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:64]


def _build_taste_text(reviews, album_statuses, song_statuses, preferences: dict | None = None) -> str:
    """
    Construct a rich natural-language description of the user's music taste.
    This text is embedded by OpenAI and stored as the taste_embedding vector.
    The richer the text, the more semantically precise the ANN queries.

    Signal hierarchy (highest weight first):
      1. Highly-rated reviews (rating >= 4.0)
      2. Favorited albums / songs
      3. Audio-feature descriptors from listened songs (Spotify features)
      4. Genre distribution across liked items
      5. Explicit preferences (genres, moods, free-text)
    """
    parts = ["Music taste profile:"]

    # Top-rated reviews — sorted by rating descending, cap at 12
    for rev in sorted(reviews, key=lambda r: -(r.rating or 0))[:12]:
        if rev.album and getattr(rev.album, "artist", None):
            parts.append(f"Rated {rev.album.title} by {rev.album.artist.name} {rev.rating}/5")
        elif rev.song and getattr(rev.song, "artist", None):
            parts.append(f"Rated {rev.song.title} by {rev.song.artist.name} {rev.rating}/5")

    # Favorited albums
    for st in album_statuses:
        if st.status == "favorites" and st.album:
            a = getattr(st.album, "artist", None)
            parts.append(f"Favorited album {st.album.title}" + (f" by {a.name}" if a else ""))

    # Favorited songs + audio-feature descriptors
    for st in song_statuses:
        if st.status == "favorites" and st.song:
            a    = getattr(st.song, "artist", None)
            base = f"Favorited song {st.song.title}" + (f" by {a.name}" if a else "")
            # Translate numeric Spotify audio features into adjectives so the
            # embedding captures *how* the music sounds, not just what it is.
            descriptors = []
            song = st.song
            if getattr(song, "energy", None) is not None:
                if song.energy > 0.75:   descriptors.append("high-energy")
                elif song.energy < 0.3:  descriptors.append("low-energy")
            if getattr(song, "valence", None) is not None:
                if song.valence > 0.7:   descriptors.append("upbeat")
                elif song.valence < 0.3: descriptors.append("melancholic")
            if getattr(song, "danceability", None) is not None and song.danceability > 0.7:
                descriptors.append("danceable")
            if getattr(song, "acousticness", None) is not None and song.acousticness > 0.7:
                descriptors.append("acoustic")
            if descriptors:
                base += f" ({', '.join(descriptors)})"
            parts.append(base)

    # Genre distribution from items rated >= 4.0
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

    # Explicit user preferences (highest signal when present)
    if preferences:
        if genres := preferences.get('genres', []):
            parts.append(f"Stated favorite genres: {', '.join(genres)}")
        if moods := preferences.get('moods', []):
            parts.append(f"Music vibe preferences: {', '.join(moods)}")
        if ft := preferences.get('free_text', '').strip():
            parts.append(f"Taste description: {ft}")

    return ". ".join(parts)


def _round_robin_merge(sets: list[list[dict]], limit: int) -> list[dict]:
    """Interleave results from multiple clusters, deduplicating by id."""
    seen: set[int] = set()
    result: list[dict] = []
    indices = [0] * len(sets)
    while len(result) < limit:
        made_progress = False
        for i, items in enumerate(sets):
            while indices[i] < len(items):
                item = items[indices[i]]
                indices[i] += 1
                if item["id"] not in seen:
                    seen.add(item["id"])
                    result.append(item)
                    made_progress = True
                    break
        if not made_progress:
            break
    return result[:limit]


def _get_cached_embedding(user: models.User, fingerprint: str) -> Optional[list[float]]:
    """Return the stored taste embedding only if the profile fingerprint still matches."""
    if user.taste_profile_hash == fingerprint and user.taste_embedding is not None:
        return list(user.taste_embedding)
    return None


async def _refresh_taste_embedding_bg(user_id: int, taste_text: str, fingerprint: str) -> None:
    """Background task: call OpenAI and persist the result — never blocks the request."""
    from ..embeddings import get_embedding

    _taste_bg_inflight.add(user_id)
    try:
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
    finally:
        _taste_bg_inflight.discard(user_id)


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
    """
    Run two ANN queries (albums + songs) against the pgvector HNSW index using
    cosine distance.  Results below MIN_SIMILARITY are filtered out so the
    caller never surfaces low-confidence matches.

    We over-fetch by 2× then apply the threshold filter, ensuring the final
    list can fill `album_limit` / `song_limit` even when some rows are pruned.
    """
    vec = _vec_literal(centroid)
    excl_albums = list(seen_album_ids) or [-1]
    excl_songs  = list(seen_song_ids)  or [-1]
    # Over-fetch to compensate for threshold pruning
    fetch_albums = album_limit * 2 + 4
    fetch_songs  = song_limit  * 2 + 4

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
        {"emb": vec, "excl_albums": excl_albums, "lim": fetch_albums},
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
        {"emb": vec, "excl_songs": excl_songs, "lim": fetch_songs},
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
        if float(r.similarity) >= MIN_SIMILARITY
    ][:album_limit]

    songs = [
        {
            "id": r.id, "title": r.title,
            "artist": {"id": r.artist_id, "name": r.artist_name},
            "album": {"id": r.album_id, "title": r.album_title, "cover_url": r.cover_url} if r.album_id else None,
            "similarity": round(float(r.similarity), 3),
            "reason": _similarity_reason(float(r.similarity)),
        }
        for r in song_rows
        if float(r.similarity) >= MIN_SIMILARITY
    ][:song_limit]

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

    # ── Load user interactions ─────────────────────────────────────────────────
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

    # Count how many catalogue items have embeddings (diagnostic / UI metadata)
    from sqlalchemy import func as _func
    album_embedding_count = db.query(_func.count(models.Album.id)).filter(models.Album.embedding.isnot(None)).scalar() or 0
    song_embedding_count  = db.query(_func.count(models.Song.id)).filter(models.Song.embedding.isnot(None)).scalar() or 0
    embedding_count = album_embedding_count + song_embedding_count

    # ── Build "seen" exclusion sets ────────────────────────────────────────────
    seen_album_ids: set[int] = set()
    seen_song_ids: set[int] = set()

    for r in reviews:
        if r.album_id: seen_album_ids.add(r.album_id)
        if r.song_id:  seen_song_ids.add(r.song_id)

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
            if li.album_id: seen_album_ids.add(li.album_id)
            if li.song_id:  seen_song_ids.add(li.song_id)

    profile_size = len(reviews) + len(album_statuses) + len(song_statuses)

    # ── Parse user music preferences ──────────────────────────────────────────
    try:
        preferences: dict = json.loads(current_user.music_preferences or '{}')
    except Exception:
        preferences = {}

    pref_genres    = preferences.get('genres', [])
    pref_moods     = preferences.get('moods', [])
    pref_free_text = preferences.get('free_text', '').strip()

    # Build one text string per preference cluster for diverse embeddings
    interest_texts = (
        [f"Music genre: {g}" for g in pref_genres]
        + [f"Music vibe and mood: {m}" for m in pref_moods]
        + ([pref_free_text] if pref_free_text else [])
    )

    # ── Fetch preference cluster embeddings (cache-only in hot path) ──────────
    # Never call OpenAI here — use whatever is already cached, and queue a
    # background task to warm any missing entries for the next request.
    from ..embeddings import is_embedding_cooling_down
    pref_vecs: list[list[float]] = []
    missing_pref_texts: list[str] = []
    for t in interest_texts:
        if t in _pref_embedding_cache:
            pref_vecs.append(_pref_embedding_cache[t])
        elif t not in _pref_bg_inflight and not is_embedding_cooling_down(t):
            missing_pref_texts.append(t)
    if missing_pref_texts:
        background_tasks.add_task(_fetch_pref_embeddings_bg, missing_pref_texts)

    # ── Helper: run vector queries for each cluster then round-robin merge ─────
    def _exec_multi(all_vecs: list, src: str):
        per = max(album_limit, song_limit) + 3
        album_sets, song_sets = [], []
        for vec in all_vecs:
            albs, sngs = _vector_recs(db, vec, seen_album_ids, seen_song_ids, per, per)
            album_sets.append(albs)
            song_sets.append(sngs)
        return (
            _round_robin_merge(album_sets, album_limit),
            _round_robin_merge(song_sets, song_limit),
            src,
        )

    # ── Taste embedding path ───────────────────────────────────────────────────
    taste_vec: Optional[list[float]] = None
    if profile_size >= _MIN_PROFILE_SIZE:
        fp = _profile_fingerprint(reviews, album_statuses, song_statuses, preferences or None)
        taste_vec = _get_cached_embedding(current_user, fp)

        if taste_vec is None:
            taste_text = _build_taste_text(reviews, album_statuses, song_statuses, preferences or None)
            if taste_text != "Music taste profile:" and uid not in _taste_bg_inflight:
                background_tasks.add_task(_refresh_taste_embedding_bg, uid, taste_text, fp)

    def _resp(albums, songs, src):
        return {
            "albums": albums,
            "songs": songs,
            "source": src,
            "profile_size": profile_size,
            "embedding_count": embedding_count,
        }

    if taste_vec:
        all_vecs = [taste_vec] + pref_vecs
        if len(all_vecs) >= 2:
            albums, songs, src = _exec_multi(all_vecs, "preferences")
        else:
            albums, songs = _vector_recs(db, taste_vec, seen_album_ids, seen_song_ids, album_limit, song_limit)
            src = "embedding"
        # If the similarity threshold pruned too aggressively, pad with fallback
        if len(albums) < album_limit // 2 or len(songs) < song_limit // 2:
            fb_albums, fb_songs = _fallback_recs(db, seen_album_ids | {a["id"] for a in albums},
                                                  seen_song_ids  | {s["id"] for s in songs},
                                                  album_limit - len(albums), song_limit - len(songs))
            albums = albums + fb_albums
            songs  = songs  + fb_songs
        return _resp(albums, songs, src)

    # ── Weighted centroid from item embeddings ────────────────────────────────
    if profile_size >= _MIN_PROFILE_SIZE:
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
                all_vecs = [centroid] + pref_vecs
                if len(all_vecs) >= 2:
                    albums, songs, src = _exec_multi(all_vecs, "preferences")
                else:
                    albums, songs = _vector_recs(db, centroid, seen_album_ids, seen_song_ids, album_limit, song_limit)
                    src = "centroid"
                return _resp(albums, songs, src)

    # ── Preferences-only path (no listening history yet) ─────────────────────
    if pref_vecs:
        if len(pref_vecs) >= 2:
            albums, songs, src = _exec_multi(pref_vecs, "preferences")
        else:
            albums, songs = _vector_recs(db, pref_vecs[0], seen_album_ids, seen_song_ids, album_limit, song_limit)
            src = "preferences"
        return _resp(albums, songs, src)

    # ── Community top-rated fallback ──────────────────────────────────────────
    albums, songs = _fallback_recs(db, seen_album_ids, seen_song_ids, album_limit, song_limit)
    return _resp(albums, songs, "fallback")
