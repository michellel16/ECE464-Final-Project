from fastapi import APIRouter, Depends
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
