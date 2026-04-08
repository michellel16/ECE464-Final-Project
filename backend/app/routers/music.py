from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List

from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_user_optional
from .search import _enrich_missing_images

router = APIRouter(prefix="/api/music", tags=["music"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _avg_rating(db, *, album_id=None, song_id=None):
    q = db.query(func.avg(models.Review.rating))
    if album_id:
        q = q.filter(models.Review.album_id == album_id)
    elif song_id:
        q = q.filter(models.Review.song_id == song_id)
    val = q.scalar()
    return round(float(val), 2) if val else None


def _review_count(db, *, album_id=None, song_id=None):
    q = db.query(func.count(models.Review.id))
    if album_id:
        q = q.filter(models.Review.album_id == album_id)
    elif song_id:
        q = q.filter(models.Review.song_id == song_id)
    return q.scalar() or 0


def _batch_album_stats(db, album_ids: list) -> tuple[dict, dict, dict]:
    """Returns (avg_map, count_map, song_count_map) keyed by album_id."""
    if not album_ids:
        return {}, {}, {}
    avg_map: dict[int, float | None] = {}
    count_map: dict[int, int] = {}
    for album_id, avg, cnt in (
        db.query(models.Review.album_id, func.avg(models.Review.rating), func.count(models.Review.id))
        .filter(models.Review.album_id.in_(album_ids))
        .group_by(models.Review.album_id)
        .all()
    ):
        avg_map[album_id] = round(float(avg), 2) if avg else None
        count_map[album_id] = cnt
    song_count_map = dict(
        db.query(models.Song.album_id, func.count(models.Song.id))
        .filter(models.Song.album_id.in_(album_ids))
        .group_by(models.Song.album_id)
        .all()
    )
    return avg_map, count_map, song_count_map


def _recency(dt) -> float:
    """Boost weight for recent interactions."""
    if not dt:
        return 1.0
    days = max(0, (datetime.utcnow() - dt).days)
    if days <= 7:   return 2.0
    if days <= 30:  return 1.5
    if days <= 90:  return 1.2
    return 1.0


_STATUS_WEIGHTS = {"favorites": 3.0, "listened": 1.5, "want_to_listen": 0.5}


def _build_affinity(uid: int, db: Session):
    """
    Aggregate every signal of user taste into per-artist scores, then derive
    weighted genre counts from those artists.

    Signals (all multiplied by a recency factor):
    - Reviews:          (rating / 5) × 3.0 × recency
    - Album statuses:   favorites 3.0 | listened 1.5 | want_to_listen 0.5  × recency
    - Song statuses:    same weights × recency
    - List additions:   1.0 × recency

    Returns:
        artist_scores          dict[artist_id → float]
        liked_artist_ids       set of artist IDs with score >= 1.0
        liked_genre_counts     dict[genre_id → float]  (sum of artist scores per genre)
        genre_to_liked_artists dict[genre_id → list[str]]  (artist names, best-score first)
    """
    artist_scores: dict[int, float] = {}

    def _add(artist_id, score):
        if artist_id:
            artist_scores[artist_id] = artist_scores.get(artist_id, 0.0) + score

    # Reviews — weighted by rating and recency
    for rating, created_at, alb_artist, sng_artist in (
        db.query(
            models.Review.rating,
            models.Review.created_at,
            models.Album.artist_id,
            models.Song.artist_id,
        )
        .outerjoin(models.Album, models.Review.album_id == models.Album.id)
        .outerjoin(models.Song,  models.Review.song_id  == models.Song.id)
        .filter(models.Review.user_id == uid)
        .all()
    ):
        _add(alb_artist or sng_artist, (rating / 5.0) * 3.0 * _recency(created_at))

    # Album statuses
    for status, created_at, artist_id in (
        db.query(
            models.UserAlbumStatus.status,
            models.UserAlbumStatus.created_at,
            models.Album.artist_id,
        )
        .join(models.Album, models.UserAlbumStatus.album_id == models.Album.id)
        .filter(models.UserAlbumStatus.user_id == uid)
        .all()
    ):
        w = _STATUS_WEIGHTS.get(status, 0)
        if w:
            _add(artist_id, w * _recency(created_at))

    # Song statuses
    for status, created_at, artist_id in (
        db.query(
            models.UserSongStatus.status,
            models.UserSongStatus.created_at,
            models.Song.artist_id,
        )
        .join(models.Song, models.UserSongStatus.song_id == models.Song.id)
        .filter(models.UserSongStatus.user_id == uid)
        .all()
    ):
        w = _STATUS_WEIGHTS.get(status, 0)
        if w:
            _add(artist_id, w * _recency(created_at))

    # List items (user curated = clear positive signal)
    list_ids = [r[0] for r in db.query(models.List.id).filter_by(user_id=uid).all()]
    if list_ids:
        for added_at, artist_id in (
            db.query(models.ListItem.added_at, models.Album.artist_id)
            .join(models.Album, models.ListItem.album_id == models.Album.id)
            .filter(models.ListItem.list_id.in_(list_ids), models.ListItem.album_id.isnot(None))
            .all()
        ):
            _add(artist_id, 1.0 * _recency(added_at))

        for added_at, artist_id in (
            db.query(models.ListItem.added_at, models.Song.artist_id)
            .join(models.Song, models.ListItem.song_id == models.Song.id)
            .filter(models.ListItem.list_id.in_(list_ids), models.ListItem.song_id.isnot(None))
            .all()
        ):
            _add(artist_id, 1.0 * _recency(added_at))

    # Build genre affinity from artists with a meaningful positive score
    liked_artist_ids = {aid for aid, s in artist_scores.items() if s >= 1.0}
    liked_genre_counts: dict[int, float] = {}
    genre_to_liked_artists: dict[int, list] = {}  # genre_id → [(name, score), ...]

    if liked_artist_ids:
        for artist in (
            db.query(models.Artist)
            .options(joinedload(models.Artist.genres))
            .filter(models.Artist.id.in_(liked_artist_ids))
            .all()
        ):
            score = artist_scores[artist.id]
            for g in artist.genres:
                liked_genre_counts[g.id] = liked_genre_counts.get(g.id, 0.0) + score
                genre_to_liked_artists.setdefault(g.id, []).append((artist.name, score))

    # Sort each genre's artists by score so the best match comes first
    genre_to_liked_artists = {
        gid: [name for name, _ in sorted(artists, key=lambda x: -x[1])]
        for gid, artists in genre_to_liked_artists.items()
    }

    return artist_scores, liked_artist_ids, liked_genre_counts, genre_to_liked_artists


def _diverse_pick(items, limit: int, get_artist_id, get_genre_ids,
                  max_per_artist: int = 1, max_per_genre: int = 2) -> list:
    """
    Greedy diversity filter: iterate items in score order, skipping any that
    would exceed the per-artist or per-genre caps.  This ensures the final
    list spans multiple artists and genres rather than clustering.
    """
    artist_count: dict[int, int] = {}
    genre_count:  dict[int, int] = {}
    result = []

    for item in items:
        aid  = get_artist_id(item)
        gids = get_genre_ids(item)

        if artist_count.get(aid, 0) >= max_per_artist:
            continue
        # Skip only when every genre for this item is already at the cap
        if gids and all(genre_count.get(gid, 0) >= max_per_genre for gid in gids):
            continue

        result.append(item)
        artist_count[aid] = artist_count.get(aid, 0) + 1
        for gid in gids:
            genre_count[gid] = genre_count.get(gid, 0) + 1

        if len(result) >= limit:
            break

    return result


# ── Genres ───────────────────────────────────────────────────────────────────

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    return db.query(models.Genre).all()


# ── Artists ───────────────────────────────────────────────────────────────────

@router.get("/artists")
def list_artists(skip: int = 0, limit: int = 50, sort: Optional[str] = None, db: Session = Depends(get_db)):
    if sort == 'recently_reviewed':
        album_latest = (
            db.query(models.Album.artist_id, func.max(models.Review.created_at).label('latest'))
            .join(models.Review, models.Review.album_id == models.Album.id)
            .group_by(models.Album.artist_id)
            .subquery()
        )
        song_latest = (
            db.query(models.Song.artist_id, func.max(models.Review.created_at).label('latest'))
            .join(models.Review, models.Review.song_id == models.Song.id)
            .group_by(models.Song.artist_id)
            .subquery()
        )
        ordered_ids = [row[0] for row in (
            db.query(models.Artist.id)
            .outerjoin(album_latest, album_latest.c.artist_id == models.Artist.id)
            .outerjoin(song_latest, song_latest.c.artist_id == models.Artist.id)
            .order_by(func.greatest(album_latest.c.latest, song_latest.c.latest).desc().nullslast())
            .limit(limit).all()
        )]
        id_map = {a.id: a for a in (
            db.query(models.Artist)
            .options(joinedload(models.Artist.genres))
            .filter(models.Artist.id.in_(ordered_ids))
            .all()
        )}
        artists = [id_map[i] for i in ordered_ids if i in id_map]
    else:
        artists = (
            db.query(models.Artist)
            .options(joinedload(models.Artist.genres))
            .offset(skip).limit(limit).all()
        )
    artist_ids = [a.id for a in artists]
    album_counts = dict(
        db.query(models.Album.artist_id, func.count(models.Album.id))
        .filter(models.Album.artist_id.in_(artist_ids))
        .group_by(models.Album.artist_id)
        .all()
    ) if artist_ids else {}
    return [
        {
            "id": a.id, "name": a.name, "bio": a.bio,
            "image_url": a.image_url, "formed_year": a.formed_year,
            "country": a.country,
            "genres": [{"id": g.id, "name": g.name} for g in a.genres],
            "album_count": album_counts.get(a.id, 0),
        }
        for a in artists
    ]


@router.get("/recommended")
def recommended_combined(
    artist_limit: int = 6,
    song_limit: int = 6,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return recommended artists + songs in a single request (shared affinity build)."""
    uid = current_user.id
    artist_scores, liked_artist_ids, liked_genre_counts, genre_to_liked_artists = \
        _build_affinity(uid, db)

    liked_genre_ids = set(liked_genre_counts)
    interacted_ids = set(artist_scores.keys())

    # ── Artists ──────────────────────────────────────────────────────────────
    artist_candidates = (
        db.query(models.Artist)
        .options(joinedload(models.Artist.genres))
        .filter(~models.Artist.id.in_(interacted_ids))
        .all()
    )

    def _artist_score(a: models.Artist) -> float:
        return sum(liked_genre_counts[g.id] for g in a.genres if g.id in liked_genre_ids)

    def _artist_reason(a: models.Artist) -> str:
        best = max((g for g in a.genres if g.id in liked_genre_ids),
                   key=lambda g: liked_genre_counts[g.id], default=None)
        if best:
            similar = genre_to_liked_artists.get(best.id, [])
            return f"Similar to {similar[0]}" if similar else f"Based on your love of {best.name}"
        return "You might enjoy this"

    sorted_artists = [a for a in sorted(artist_candidates, key=_artist_score, reverse=True) if _artist_score(a) > 0]
    top_artists = _diverse_pick(
        sorted_artists, artist_limit,
        get_artist_id=lambda a: a.id,
        get_genre_ids=lambda a: [g.id for g in a.genres],
        max_per_artist=1, max_per_genre=2,
    )

    # ── Songs ─────────────────────────────────────────────────────────────────
    seen_song_ids: set[int] = {
        row[0] for row in
        db.query(models.Review.song_id)
        .filter(models.Review.user_id == uid, models.Review.song_id.isnot(None))
        .all()
    } | {
        row[0] for row in
        db.query(models.UserSongStatus.song_id)
        .filter(models.UserSongStatus.user_id == uid)
        .all()
    }
    interacted_album_ids: set[int] = {
        row[0] for row in
        db.query(models.UserAlbumStatus.album_id)
        .filter(models.UserAlbumStatus.user_id == uid)
        .all()
    }
    if interacted_album_ids:
        seen_song_ids |= {
            row[0] for row in
            db.query(models.Song.id)
            .filter(models.Song.album_id.in_(interacted_album_ids))
            .all()
        }
    list_ids = [r[0] for r in db.query(models.List.id).filter_by(user_id=uid).all()]
    if list_ids:
        seen_song_ids |= {
            row[0] for row in
            db.query(models.ListItem.song_id)
            .filter(models.ListItem.list_id.in_(list_ids), models.ListItem.song_id.isnot(None))
            .all()
        }

    avg_ratings: dict[int, float] = {
        sid: float(avg)
        for sid, avg in db.query(models.Review.song_id, func.avg(models.Review.rating))
        .filter(models.Review.song_id.isnot(None))
        .group_by(models.Review.song_id)
        .all()
    }

    song_candidates = (
        db.query(models.Song)
        .options(
            joinedload(models.Song.artist).joinedload(models.Artist.genres),
            joinedload(models.Song.album),
        )
        .filter(~models.Song.id.in_(seen_song_ids) if seen_song_ids else True)
        .all()
    )

    def _song_score(s: models.Song) -> float:
        score = sum(
            liked_genre_counts[g.id]
            for g in (s.artist.genres if s.artist else [])
            if g.id in liked_genre_ids
        )
        score += artist_scores.get(s.artist_id, 0.0) * 0.5
        score += avg_ratings.get(s.id, 0.0)
        return score

    def _song_reason(s: models.Song) -> str:
        if artist_scores.get(s.artist_id, 0.0) >= 1.0:
            return f"Because you like {s.artist.name}"
        best = max(
            (g for g in (s.artist.genres if s.artist else []) if g.id in liked_genre_ids),
            key=lambda g: liked_genre_counts[g.id], default=None,
        )
        if best:
            similar = genre_to_liked_artists.get(best.id, [])
            return f"Similar to {similar[0]}" if similar else f"Based on your love of {best.name}"
        r = avg_ratings.get(s.id)
        return f"Highly rated · ★ {r:.1f}" if r and r >= 4.0 else "Popular on Tunelog"

    top_songs = _diverse_pick(
        sorted(song_candidates, key=_song_score, reverse=True), song_limit,
        get_artist_id=lambda s: s.artist_id,
        get_genre_ids=lambda s: [g.id for g in (s.artist.genres if s.artist else [])],
        max_per_artist=1, max_per_genre=2,
    )

    return {
        "artists": [
            {
                "id": a.id, "name": a.name, "image_url": a.image_url,
                "genres": [g.name for g in a.genres],
                "reason": _artist_reason(a),
            }
            for a in top_artists
        ],
        "songs": [
            {
                "id": s.id, "title": s.title,
                "artist": {"id": s.artist.id, "name": s.artist.name},
                "album": {"id": s.album.id, "title": s.album.title, "cover_url": s.album.cover_url} if s.album else None,
                "average_rating": round(avg_ratings[s.id], 2) if s.id in avg_ratings else None,
                "reason": _song_reason(s),
            }
            for s in top_songs
        ],
    }


@router.get("/artists/recommended")
def recommended_artists(
    limit: int = 6,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id
    artist_scores, liked_artist_ids, liked_genre_counts, genre_to_liked_artists = \
        _build_affinity(uid, db)

    # Exclude every artist the user has any interaction with
    interacted_ids = set(artist_scores.keys())

    liked_genre_ids = set(liked_genre_counts)

    candidates = (
        db.query(models.Artist)
        .options(joinedload(models.Artist.genres))
        .filter(~models.Artist.id.in_(interacted_ids))
        .all()
    )

    def _score(artist: models.Artist) -> float:
        return sum(liked_genre_counts[g.id] for g in artist.genres if g.id in liked_genre_ids)

    def _reason(artist: models.Artist) -> str:
        best_genre = max(
            (g for g in artist.genres if g.id in liked_genre_ids),
            key=lambda g: liked_genre_counts[g.id],
            default=None,
        )
        if best_genre:
            similar = genre_to_liked_artists.get(best_genre.id, [])
            if similar:
                return f"Similar to {similar[0]}"
            return f"Based on your love of {best_genre.name}"
        return "You might enjoy this"

    sorted_candidates = [a for a in sorted(candidates, key=_score, reverse=True) if _score(a) > 0]
    top = _diverse_pick(
        sorted_candidates, limit,
        get_artist_id=lambda a: a.id,
        get_genre_ids=lambda a: [g.id for g in a.genres],
        max_per_artist=1,
        max_per_genre=2,
    )

    return [
        {
            "id": a.id,
            "name": a.name,
            "image_url": a.image_url,
            "genres": [g.name for g in a.genres],
            "reason": _reason(a),
        }
        for a in top
    ]


@router.get("/artists/{artist_id}")
async def get_artist(artist_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Artist not found")
    await _enrich_missing_images(db, [a], [])
    return {
        "id": a.id, "name": a.name, "bio": a.bio,
        "image_url": a.image_url, "formed_year": a.formed_year,
        "country": a.country,
        "genres": [{"id": g.id, "name": g.name} for g in a.genres],
        "album_count": len(a.albums),
    }


@router.get("/artists/{artist_id}/albums")
def get_artist_albums(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    albums = (
        db.query(models.Album)
        .options(joinedload(models.Album.genres))
        .filter(models.Album.artist_id == artist_id)
        .all()
    )
    album_ids = [al.id for al in albums]
    avg_map, count_map, song_count_map = _batch_album_stats(db, album_ids)
    return [
        {
            "id": al.id, "title": al.title, "artist_id": al.artist_id,
            "release_date": al.release_date, "cover_url": al.cover_url,
            "description": al.description,
            "genres": [{"id": g.id, "name": g.name} for g in al.genres],
            "average_rating": avg_map.get(al.id),
            "review_count": count_map.get(al.id, 0),
            "song_count": song_count_map.get(al.id, 0),
        }
        for al in albums
    ]


# ── Albums ────────────────────────────────────────────────────────────────────

@router.get("/albums")
def list_albums(skip: int = 0, limit: int = 30, sort: Optional[str] = None, db: Session = Depends(get_db)):
    if sort == 'recently_reviewed':
        latest_review = (
            db.query(models.Review.album_id, func.max(models.Review.created_at).label('latest'))
            .filter(models.Review.album_id.isnot(None))
            .group_by(models.Review.album_id)
            .subquery()
        )
        ordered_ids = [row[0] for row in (
            db.query(models.Album.id)
            .outerjoin(latest_review, latest_review.c.album_id == models.Album.id)
            .order_by(latest_review.c.latest.desc().nullslast())
            .limit(limit).all()
        )]
        id_map = {al.id: al for al in (
            db.query(models.Album)
            .options(joinedload(models.Album.artist), joinedload(models.Album.genres))
            .filter(models.Album.id.in_(ordered_ids))
            .all()
        )}
        albums = [id_map[i] for i in ordered_ids if i in id_map]
    else:
        albums = (
            db.query(models.Album)
            .options(joinedload(models.Album.artist), joinedload(models.Album.genres))
            .offset(skip).limit(limit).all()
        )
    album_ids = [al.id for al in albums]
    avg_map, count_map, _ = _batch_album_stats(db, album_ids)
    return [
        {
            "id": al.id, "title": al.title, "artist_id": al.artist_id,
            "artist": {"id": al.artist.id, "name": al.artist.name, "image_url": al.artist.image_url} if al.artist else None,
            "release_date": al.release_date, "cover_url": al.cover_url,
            "description": al.description,
            "genres": [{"id": g.id, "name": g.name} for g in al.genres],
            "average_rating": avg_map.get(al.id),
            "review_count": count_map.get(al.id, 0),
        }
        for al in albums
    ]


@router.get("/albums/{album_id}")
async def get_album(album_id: int, db: Session = Depends(get_db)):
    al = (
        db.query(models.Album)
        .options(
            joinedload(models.Album.artist),
            joinedload(models.Album.genres),
            joinedload(models.Album.songs),
        )
        .filter(models.Album.id == album_id)
        .first()
    )
    if not al:
        raise HTTPException(status_code=404, detail="Album not found")
    await _enrich_missing_images(db, [al.artist] if al.artist else [], [al])
    song_ids = [s.id for s in al.songs]
    song_avg_map: dict[int, float] = {}
    if song_ids:
        song_avg_map = {
            sid: round(float(avg), 2)
            for sid, avg in (
                db.query(models.Review.song_id, func.avg(models.Review.rating))
                .filter(models.Review.song_id.in_(song_ids))
                .group_by(models.Review.song_id)
                .all()
            )
        }
    album_avg_map, album_count_map, _ = _batch_album_stats(db, [album_id])
    return {
        "id": al.id, "title": al.title, "artist_id": al.artist_id,
        "artist": {"id": al.artist.id, "name": al.artist.name, "image_url": al.artist.image_url} if al.artist else None,
        "release_date": al.release_date, "cover_url": al.cover_url,
        "description": al.description,
        "genres": [{"id": g.id, "name": g.name} for g in al.genres],
        "songs": [
            {
                "id": s.id, "title": s.title,
                "track_number": s.track_number, "duration_seconds": s.duration_seconds,
                "average_rating": song_avg_map.get(s.id),
                "spotify_id": s.spotify_id,
                "spotify_preview_url": s.spotify_preview_url,
            }
            for s in al.songs
        ],
        "average_rating": album_avg_map.get(album_id),
        "review_count": album_count_map.get(album_id, 0),
    }


# ── Songs ─────────────────────────────────────────────────────────────────────

@router.get("/songs")
def list_songs(skip: int = 0, limit: int = 50, sort: Optional[str] = None, db: Session = Depends(get_db)):
    if sort == 'recently_reviewed':
        latest_review = (
            db.query(models.Review.song_id, func.max(models.Review.created_at).label('latest'))
            .filter(models.Review.song_id.isnot(None))
            .group_by(models.Review.song_id)
            .subquery()
        )
        ordered_ids = [row[0] for row in (
            db.query(models.Song.id)
            .outerjoin(latest_review, latest_review.c.song_id == models.Song.id)
            .order_by(latest_review.c.latest.desc().nullslast())
            .limit(limit).all()
        )]
        id_map = {s.id: s for s in (
            db.query(models.Song)
            .options(joinedload(models.Song.artist), joinedload(models.Song.album))
            .filter(models.Song.id.in_(ordered_ids))
            .all()
        )}
        songs = [id_map[i] for i in ordered_ids if i in id_map]
    else:
        songs = (
            db.query(models.Song)
            .options(joinedload(models.Song.artist), joinedload(models.Song.album))
            .offset(skip).limit(limit).all()
        )
    song_ids = [s.id for s in songs]
    avg_map: dict[int, float] = {}
    if song_ids:
        avg_map = {
            sid: round(float(avg), 2)
            for sid, avg in (
                db.query(models.Review.song_id, func.avg(models.Review.rating))
                .filter(models.Review.song_id.in_(song_ids))
                .group_by(models.Review.song_id)
                .all()
            )
        }
    return [
        {
            "id": s.id, "title": s.title, "artist_id": s.artist_id,
            "artist": {"id": s.artist.id, "name": s.artist.name} if s.artist else None,
            "album_id": s.album_id,
            "album": {"id": s.album.id, "title": s.album.title, "cover_url": s.album.cover_url} if s.album else None,
            "duration_seconds": s.duration_seconds, "track_number": s.track_number,
            "average_rating": avg_map.get(s.id),
        }
        for s in songs
    ]


@router.get("/songs/recommended")
def recommended_songs(
    limit: int = 6,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id
    artist_scores, liked_artist_ids, liked_genre_counts, genre_to_liked_artists = \
        _build_affinity(uid, db)

    liked_genre_ids = set(liked_genre_counts)

    # Songs the user has already touched (reviews, statuses, list items, album interactions)
    seen_song_ids: set[int] = {
        row[0] for row in
        db.query(models.Review.song_id)
        .filter(models.Review.user_id == uid, models.Review.song_id.isnot(None))
        .all()
    } | {
        row[0] for row in
        db.query(models.UserSongStatus.song_id)
        .filter(models.UserSongStatus.user_id == uid)
        .all()
    }

    interacted_album_ids: set[int] = {
        row[0] for row in
        db.query(models.UserAlbumStatus.album_id)
        .filter(models.UserAlbumStatus.user_id == uid)
        .all()
    }
    if interacted_album_ids:
        seen_song_ids |= {
            row[0] for row in
            db.query(models.Song.id)
            .filter(models.Song.album_id.in_(interacted_album_ids))
            .all()
        }

    # Also exclude songs the user has added to any list
    list_ids = [r[0] for r in db.query(models.List.id).filter_by(user_id=uid).all()]
    if list_ids:
        seen_song_ids |= {
            row[0] for row in
            db.query(models.ListItem.song_id)
            .filter(models.ListItem.list_id.in_(list_ids), models.ListItem.song_id.isnot(None))
            .all()
        }

    # Global avg ratings in one query
    avg_ratings: dict[int, float] = {
        sid: float(avg)
        for sid, avg in db.query(models.Review.song_id, func.avg(models.Review.rating))
        .filter(models.Review.song_id.isnot(None))
        .group_by(models.Review.song_id)
        .all()
    }

    candidates = (
        db.query(models.Song)
        .options(
            joinedload(models.Song.artist).joinedload(models.Artist.genres),
            joinedload(models.Song.album),
        )
        .filter(~models.Song.id.in_(seen_song_ids) if seen_song_ids else True)
        .all()
    )

    def _score(song: models.Song) -> float:
        score = sum(
            liked_genre_counts[g.id]
            for g in (song.artist.genres if song.artist else [])
            if g.id in liked_genre_ids
        )
        score += artist_scores.get(song.artist_id, 0.0) * 0.5
        score += avg_ratings.get(song.id, 0.0)
        return score

    def _reason(song: models.Song) -> str:
        a_score = artist_scores.get(song.artist_id, 0.0)
        if a_score >= 1.0:
            return f"Because you like {song.artist.name}"
        best_genre = max(
            (g for g in (song.artist.genres if song.artist else []) if g.id in liked_genre_ids),
            key=lambda g: liked_genre_counts[g.id],
            default=None,
        )
        if best_genre:
            similar = genre_to_liked_artists.get(best_genre.id, [])
            if similar:
                return f"Similar to {similar[0]}"
            return f"Based on your love of {best_genre.name}"
        r = avg_ratings.get(song.id)
        if r and r >= 4.0:
            return f"Highly rated · ★ {r:.1f}"
        return "Popular on Tunelog"

    sorted_candidates = sorted(candidates, key=_score, reverse=True)
    top = _diverse_pick(
        sorted_candidates, limit,
        get_artist_id=lambda s: s.artist_id,
        get_genre_ids=lambda s: [g.id for g in (s.artist.genres if s.artist else [])],
        max_per_artist=1,
        max_per_genre=2,
    )

    return [
        {
            "id": s.id,
            "title": s.title,
            "artist": {"id": s.artist.id, "name": s.artist.name},
            "album": {
                "id": s.album.id,
                "title": s.album.title,
                "cover_url": s.album.cover_url,
            } if s.album else None,
            "average_rating": round(avg_ratings[s.id], 2) if s.id in avg_ratings else None,
            "reason": _reason(s),
        }
        for s in top
    ]


@router.get("/songs/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Song not found")
    return {
        "id": s.id, "title": s.title, "artist_id": s.artist_id,
        "artist": {"id": s.artist.id, "name": s.artist.name, "image_url": s.artist.image_url},
        "album_id": s.album_id,
        "album": {"id": s.album.id, "title": s.album.title, "cover_url": s.album.cover_url} if s.album else None,
        "duration_seconds": s.duration_seconds, "track_number": s.track_number,
        "average_rating": _avg_rating(db, song_id=s.id),
        "review_count": _review_count(db, song_id=s.id),
        "spotify_id": s.spotify_id,
        "spotify_preview_url": s.spotify_preview_url,
        "danceability": s.danceability, "energy": s.energy, "valence": s.valence,
        "loudness": s.loudness, "tempo": s.tempo, "acousticness": s.acousticness,
        "instrumentalness": s.instrumentalness,
    }


# ── Reviews ───────────────────────────────────────────────────────────────────

def _review_row(r: models.Review, like_count: int = 0, liked_by_me: bool = False) -> dict:
    return {
        "id": r.id, "user_id": r.user_id, "username": r.user.username,
        "avatar_url": r.user.avatar_url,
        "song_id": r.song_id, "album_id": r.album_id,
        "text": r.text, "rating": r.rating, "created_at": r.created_at,
        "like_count": like_count,
        "liked_by_me": liked_by_me,
    }


def _enrich_reviews(
    rows: list, db: Session, current_user: Optional[models.User] = None
) -> list:
    if not rows:
        return []
    review_ids = [r.id for r in rows]
    like_counts = dict(
        db.query(models.ReviewLike.review_id, func.count())
        .filter(models.ReviewLike.review_id.in_(review_ids))
        .group_by(models.ReviewLike.review_id)
        .all()
    )
    liked_set: set[int] = set()
    if current_user:
        liked_set = {
            row[0] for row in
            db.query(models.ReviewLike.review_id)
            .filter(
                models.ReviewLike.review_id.in_(review_ids),
                models.ReviewLike.user_id == current_user.id,
            )
            .all()
        }
    return [
        _review_row(r, like_count=like_counts.get(r.id, 0), liked_by_me=r.id in liked_set)
        for r in rows
    ]


@router.get("/albums/{album_id}/reviews")
def get_album_reviews(
    album_id: int, skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.Review)
        .filter(models.Review.album_id == album_id)
        .order_by(models.Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return _enrich_reviews(rows, db, current_user)


@router.post("/albums/{album_id}/reviews", status_code=201)
def create_album_review(
    album_id: int,
    review: schemas.ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.query(models.Album).filter(models.Album.id == album_id).first():
        raise HTTPException(status_code=404, detail="Album not found")

    existing = db.query(models.Review).filter_by(user_id=current_user.id, album_id=album_id).first()
    if existing:
        existing.text = review.text
        existing.rating = review.rating
        db.commit()
        db.refresh(existing)
        from ..embeddings import reembed_album_bg
        background_tasks.add_task(reembed_album_bg, album_id)
        return _review_row(existing)

    r = models.Review(user_id=current_user.id, album_id=album_id, text=review.text, rating=review.rating)
    db.add(r)
    db.add(models.Activity(
        user_id=current_user.id, action_type="reviewed_album",
        target_type="album", target_id=album_id,
        meta=f'{{"rating":{review.rating}}}',
    ))
    db.commit()
    db.refresh(r)
    from ..embeddings import reembed_album_bg
    background_tasks.add_task(reembed_album_bg, album_id)
    return _review_row(r)


@router.get("/songs/{song_id}/reviews")
def get_song_reviews(
    song_id: int, skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    rows = (
        db.query(models.Review)
        .filter(models.Review.song_id == song_id)
        .order_by(models.Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return _enrich_reviews(rows, db, current_user)


@router.post("/songs/{song_id}/reviews", status_code=201)
def create_song_review(
    song_id: int,
    review: schemas.ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.query(models.Song).filter(models.Song.id == song_id).first():
        raise HTTPException(status_code=404, detail="Song not found")

    existing = db.query(models.Review).filter_by(user_id=current_user.id, song_id=song_id).first()
    if existing:
        existing.text = review.text
        existing.rating = review.rating
        db.commit()
        db.refresh(existing)
        from ..embeddings import reembed_song_bg
        background_tasks.add_task(reembed_song_bg, song_id)
        return _review_row(existing)

    r = models.Review(user_id=current_user.id, song_id=song_id, text=review.text, rating=review.rating)
    db.add(r)
    db.add(models.Activity(
        user_id=current_user.id, action_type="reviewed_song",
        target_type="song", target_id=song_id,
        meta=f'{{"rating":{review.rating}}}',
    ))
    db.commit()
    db.refresh(r)
    from ..embeddings import reembed_song_bg
    background_tasks.add_task(reembed_song_bg, song_id)
    return _review_row(r)


# ── User review on album/song ────────────────────────────────────────────────

@router.get("/albums/{album_id}/my-review")
def my_album_review(album_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    r = db.query(models.Review).filter_by(user_id=current_user.id, album_id=album_id).first()
    return {"review": _review_row(r) if r else None}


@router.get("/songs/{song_id}/my-review")
def my_song_review(song_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    r = db.query(models.Review).filter_by(user_id=current_user.id, song_id=song_id).first()
    return {"review": _review_row(r) if r else None}


# ── Review likes ─────────────────────────────────────────────────────────────

@router.post("/reviews/{review_id}/like")
def toggle_review_like(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    existing = db.query(models.ReviewLike).filter_by(
        user_id=current_user.id, review_id=review_id
    ).first()
    if existing:
        db.delete(existing)
        liked = False
    else:
        db.add(models.ReviewLike(user_id=current_user.id, review_id=review_id))
        liked = True
    db.commit()

    count = (
        db.query(func.count(models.ReviewLike.review_id))
        .filter_by(review_id=review_id)
        .scalar() or 0
    )
    return {"liked": liked, "like_count": count}


# ── Status ────────────────────────────────────────────────────────────────────

VALID_STATUSES = {"listened", "want_to_listen", "favorites"}


@router.get("/albums/{album_id}/status")
def get_album_status(album_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    row = db.query(models.UserAlbumStatus).filter_by(user_id=current_user.id, album_id=album_id).first()
    return {"status": row.status if row else None}


@router.post("/albums/{album_id}/status")
def set_album_status(
    album_id: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_status = body.get("status")
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    if not db.query(models.Album).filter(models.Album.id == album_id).first():
        raise HTTPException(status_code=404, detail="Album not found")

    row = db.query(models.UserAlbumStatus).filter_by(user_id=current_user.id, album_id=album_id).first()
    if row:
        row.status = new_status
    else:
        db.add(models.UserAlbumStatus(user_id=current_user.id, album_id=album_id, status=new_status))

    db.add(models.Activity(
        user_id=current_user.id, action_type=f"marked_album_{new_status}",
        target_type="album", target_id=album_id,
    ))
    db.commit()
    return {"status": new_status}


@router.delete("/albums/{album_id}/status")
def remove_album_status(album_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    row = db.query(models.UserAlbumStatus).filter_by(user_id=current_user.id, album_id=album_id).first()
    if row:
        db.delete(row)
        db.commit()
    return {"status": None}


@router.get("/songs/{song_id}/status")
def get_song_status(song_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    row = db.query(models.UserSongStatus).filter_by(user_id=current_user.id, song_id=song_id).first()
    return {"status": row.status if row else None}


@router.post("/songs/{song_id}/status")
def set_song_status(
    song_id: int,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_status = body.get("status")
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    row = db.query(models.UserSongStatus).filter_by(user_id=current_user.id, song_id=song_id).first()
    if row:
        row.status = new_status
    else:
        db.add(models.UserSongStatus(user_id=current_user.id, song_id=song_id, status=new_status))
    db.commit()
    return {"status": new_status}


@router.delete("/songs/{song_id}/status")
def remove_song_status(song_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db.query(models.UserSongStatus).filter_by(user_id=current_user.id, song_id=song_id).delete()
    db.commit()
    return {"status": None}
