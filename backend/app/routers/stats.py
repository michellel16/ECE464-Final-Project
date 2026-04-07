from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/me")
def my_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    uid = current_user.id

    albums_listened = (
        db.query(func.count(models.UserAlbumStatus.album_id))
        .filter_by(user_id=uid, status="listened").scalar() or 0
    )
    songs_listened = (
        db.query(func.count(models.UserSongStatus.song_id))
        .filter_by(user_id=uid, status="listened").scalar() or 0
    )
    total_reviews = (
        db.query(func.count(models.Review.id))
        .filter_by(user_id=uid).scalar() or 0
    )
    avg_rating = (
        db.query(func.avg(models.Review.rating))
        .filter_by(user_id=uid).scalar()
    )

    # Top genres from reviewed albums
    reviewed_album_ids = [
        r[0] for r in
        db.query(models.Review.album_id)
        .filter(models.Review.user_id == uid, models.Review.album_id.isnot(None))
        .all()
    ]
    genre_counts: dict[str, int] = {}
    for aid in reviewed_album_ids:
        album = db.query(models.Album).get(aid)
        if album:
            for g in album.genres:
                genre_counts[g.name] = genre_counts.get(g.name, 0) + 1

    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Rating distribution (1–5 in 0.5 steps)
    all_ratings = [
        r[0] for r in db.query(models.Review.rating).filter_by(user_id=uid).all()
    ]
    distribution: dict[str, int] = {}
    for r in all_ratings:
        key = str(r)
        distribution[key] = distribution.get(key, 0) + 1

    # Recent reviews with target info
    recent = (
        db.query(models.Review)
        .filter_by(user_id=uid)
        .order_by(models.Review.created_at.desc())
        .limit(5).all()
    )
    recent_out = []
    for r in recent:
        row = {"id": r.id, "rating": r.rating, "text": r.text, "created_at": r.created_at}
        if r.album:
            row["target_title"]  = r.album.title
            row["target_cover"]  = r.album.cover_url
            row["target_type"]   = "album"
            row["target_id"]     = r.album_id
            row["target_artist"] = r.album.artist.name
        elif r.song:
            row["target_title"]  = r.song.title
            row["target_cover"]  = r.song.album.cover_url if r.song.album else None
            row["target_type"]   = "song"
            row["target_id"]     = r.song_id
            row["target_artist"] = r.song.artist.name
        recent_out.append(row)

    # Audio profile — averages across listened songs with Spotify feature data
    listened_song_ids = [
        row[0] for row in
        db.query(models.UserSongStatus.song_id)
        .filter_by(user_id=uid, status="listened")
        .all()
    ]
    audio_profile = None
    if listened_song_ids:
        feature_songs = (
            db.query(models.Song)
            .filter(
                models.Song.id.in_(listened_song_ids),
                models.Song.energy.isnot(None),
            )
            .all()
        )
        if feature_songs:
            n = len(feature_songs)
            avgs = {
                "energy":           round(sum(s.energy           or 0 for s in feature_songs) / n, 3),
                "danceability":     round(sum(s.danceability     or 0 for s in feature_songs) / n, 3),
                "valence":          round(sum(s.valence          or 0 for s in feature_songs) / n, 3),
                "acousticness":     round(sum(s.acousticness     or 0 for s in feature_songs) / n, 3),
                "instrumentalness": round(sum(s.instrumentalness or 0 for s in feature_songs) / n, 3),
                "tempo":            round(sum(s.tempo            or 0 for s in feature_songs) / n, 1),
            }
            audio_profile = {"songs_with_features": n, **avgs, "personality": _compute_personality(avgs)}

    return {
        "albums_listened":    albums_listened,
        "songs_listened":     songs_listened,
        "total_reviews":      total_reviews,
        "average_rating":     round(float(avg_rating), 2) if avg_rating else None,
        "top_genres":         [{"name": n, "count": c} for n, c in top_genres],
        "rating_distribution": distribution,
        "recent_reviews":     recent_out,
        "audio_profile":      audio_profile,
    }


@router.get("/me/postcard")
def postcard_stats(
    time_span: str = Query("all"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id

    span_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    cutoff = (
        datetime.utcnow() - timedelta(days=span_days[time_span])
        if time_span in span_days else None
    )

    # Counts filtered by time
    def _count_q(model, **filters):
        q = db.query(func.count()).select_from(model).filter_by(**filters)
        if cutoff is not None:
            q = q.filter(model.created_at >= cutoff)
        return q.scalar() or 0

    albums_listened = _count_q(models.UserAlbumStatus, user_id=uid, status="listened")
    songs_listened  = _count_q(models.UserSongStatus,  user_id=uid, status="listened")

    # Reviews in period
    rev_q = db.query(models.Review).filter_by(user_id=uid)
    if cutoff:
        rev_q = rev_q.filter(models.Review.created_at >= cutoff)
    reviews_in_period = rev_q.all()
    total_reviews = len(reviews_in_period)
    avg_rating = (
        round(sum(r.rating for r in reviews_in_period) / total_reviews, 2)
        if total_reviews else None
    )

    # Top songs by rating (deduplicated, highest rating wins)
    song_reviews = sorted(
        [r for r in reviews_in_period if r.song_id is not None],
        key=lambda r: r.rating, reverse=True
    )
    top_songs, seen_songs = [], set()
    for r in song_reviews:
        if r.song and r.song_id not in seen_songs:
            seen_songs.add(r.song_id)
            top_songs.append({
                "title":  r.song.title,
                "artist": r.song.artist.name if r.song.artist else None,
                "rating": r.rating,
            })
        if len(top_songs) == 5:
            break

    # Top albums by rating
    album_reviews = sorted(
        [r for r in reviews_in_period if r.album_id is not None],
        key=lambda r: r.rating, reverse=True
    )
    top_albums, seen_albums = [], set()
    for r in album_reviews:
        if r.album and r.album_id not in seen_albums:
            seen_albums.add(r.album_id)
            top_albums.append({
                "title":  r.album.title,
                "artist": r.album.artist.name if r.album.artist else None,
                "rating": r.rating,
            })
        if len(top_albums) == 3:
            break

    # Top genres from listened albums in period
    listened_aid_q = db.query(models.UserAlbumStatus.album_id).filter_by(user_id=uid, status="listened")
    if cutoff:
        listened_aid_q = listened_aid_q.filter(models.UserAlbumStatus.created_at >= cutoff)
    listened_aids = [row[0] for row in listened_aid_q.all()]
    genre_counts: dict[str, int] = {}
    for aid in listened_aids:
        album = db.query(models.Album).get(aid)
        if album:
            for g in album.genres:
                genre_counts[g.name] = genre_counts.get(g.name, 0) + 1
    top_genres = [
        {"name": n, "count": c}
        for n, c in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Audio profile from listened songs in period
    listened_sid_q = db.query(models.UserSongStatus.song_id).filter_by(user_id=uid, status="listened")
    if cutoff:
        listened_sid_q = listened_sid_q.filter(models.UserSongStatus.created_at >= cutoff)
    listened_sids = [row[0] for row in listened_sid_q.all()]
    audio_profile = None
    if listened_sids:
        feature_songs = (
            db.query(models.Song)
            .filter(models.Song.id.in_(listened_sids), models.Song.energy.isnot(None))
            .all()
        )
        if feature_songs:
            n = len(feature_songs)
            avgs = {
                "energy":           round(sum(s.energy           or 0 for s in feature_songs) / n, 3),
                "danceability":     round(sum(s.danceability     or 0 for s in feature_songs) / n, 3),
                "valence":          round(sum(s.valence          or 0 for s in feature_songs) / n, 3),
                "acousticness":     round(sum(s.acousticness     or 0 for s in feature_songs) / n, 3),
                "instrumentalness": round(sum(s.instrumentalness or 0 for s in feature_songs) / n, 3),
            }
            audio_profile = {"songs_with_features": n, **avgs, "personality": _compute_personality(avgs)}

    return {
        "top_songs":  top_songs,
        "top_albums": top_albums,
        "top_genres": top_genres,
        "audio_profile": audio_profile,
        "summary": {
            "albums_listened": albums_listened,
            "songs_listened":  songs_listened,
            "total_reviews":   total_reviews,
            "avg_rating":      avg_rating,
        },
    }


def _compute_personality(avg: dict) -> str:
    labels = []
    energy       = avg.get("energy", 0.5)
    danceability = avg.get("danceability", 0.5)
    valence      = avg.get("valence", 0.5)
    acousticness = avg.get("acousticness", 0.5)
    instrumental = avg.get("instrumentalness", 0.5)

    if energy > 0.7 and danceability > 0.6:
        labels.append("high-energy & danceable")
    elif energy > 0.7:
        labels.append("high-energy")
    elif energy < 0.35:
        labels.append("low-key & relaxed")

    if acousticness > 0.6:
        labels.append("acoustic")

    if valence < 0.35:
        labels.append("melancholic")
    elif valence > 0.7:
        labels.append("upbeat & positive")

    if instrumental > 0.5:
        labels.append("instrumental")

    if not labels:
        return "Eclectic taste"
    return " / ".join(labels).capitalize() + " music fan"
