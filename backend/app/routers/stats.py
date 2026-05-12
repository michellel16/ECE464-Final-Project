from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/me")
def my_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    uid = current_user.id

    album_ids_reviewed = {r[0] for r in db.query(models.Review.album_id)
        .filter(models.Review.user_id == uid, models.Review.album_id.isnot(None)).all()}
    album_ids_status = {r[0] for r in db.query(models.UserAlbumStatus.album_id)
        .filter_by(user_id=uid).all()}
    albums_listened = len(album_ids_reviewed | album_ids_status)

    song_ids_reviewed = {r[0] for r in db.query(models.Review.song_id)
        .filter(models.Review.user_id == uid, models.Review.song_id.isnot(None)).all()}
    song_ids_status = {r[0] for r in db.query(models.UserSongStatus.song_id)
        .filter_by(user_id=uid).all()}
    songs_listened = len(song_ids_reviewed | song_ids_status)
    total_reviews = (
        db.query(func.count(models.Review.id))
        .filter_by(user_id=uid).scalar() or 0
    )
    avg_rating = (
        db.query(func.avg(models.Review.rating))
        .filter_by(user_id=uid).scalar()
    )

    # Top genres from reviewed albums — single batch query, no loop
    reviewed_album_ids = [
        r[0] for r in
        db.query(models.Review.album_id)
        .filter(models.Review.user_id == uid, models.Review.album_id.isnot(None))
        .all()
    ]
    genre_counts: dict[str, int] = {}
    if reviewed_album_ids:
        for album in (
            db.query(models.Album)
            .options(selectinload(models.Album.genres))
            .filter(models.Album.id.in_(reviewed_album_ids))
            .all()
        ):
            for g in album.genres:
                genre_counts[g.name] = genre_counts.get(g.name, 0) + 1

    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Rating distribution — aggregate in SQL, not Python
    distribution: dict[str, int] = {
        str(rating): cnt
        for rating, cnt in
        db.query(models.Review.rating, func.count(models.Review.id))
        .filter(models.Review.user_id == uid)
        .group_by(models.Review.rating)
        .all()
    }

    # Recent reviews with target info — eager-load all relationships
    recent = (
        db.query(models.Review)
        .options(
            joinedload(models.Review.user),
            joinedload(models.Review.album).joinedload(models.Album.artist),
            joinedload(models.Review.song).joinedload(models.Song.artist),
            joinedload(models.Review.song).joinedload(models.Song.album),
        )
        .filter(models.Review.user_id == uid)
        .order_by(models.Review.created_at.desc())
        .limit(100).all()
    )
    recent_out = []
    for r in recent:
        row = {"id": r.id, "rating": r.rating, "text": r.text, "created_at": r.created_at}
        if r.album:
            row["target_title"]  = r.album.title
            row["target_cover"]  = r.album.cover_url
            row["target_type"]   = "album"
            row["target_id"]     = r.album_id
            row["target_artist"] = r.album.artist.name if r.album.artist else None
        elif r.song:
            row["target_title"]  = r.song.title
            row["target_cover"]  = r.song.album.cover_url if r.song.album else None
            row["target_type"]   = "song"
            row["target_id"]     = r.song_id
            row["target_artist"] = r.song.artist.name if r.song.artist else None
        recent_out.append(row)

    # Audio profile — use SQL AVG instead of loading all rows into Python
    listened_song_ids = [
        row[0] for row in
        db.query(models.UserSongStatus.song_id)
        .filter_by(user_id=uid, status="listened")
        .all()
    ]
    audio_profile = None
    if listened_song_ids:
        avgs_row = (
            db.query(
                func.avg(models.Song.energy).label("energy"),
                func.avg(models.Song.danceability).label("danceability"),
                func.avg(models.Song.valence).label("valence"),
                func.avg(models.Song.acousticness).label("acousticness"),
                func.avg(models.Song.instrumentalness).label("instrumentalness"),
                func.avg(models.Song.tempo).label("tempo"),
                func.count(models.Song.id).label("n"),
            )
            .filter(
                models.Song.id.in_(listened_song_ids),
                models.Song.energy.isnot(None),
            )
            .one()
        )
        if avgs_row.n:
            avgs = {
                "energy":           round(float(avgs_row.energy), 3),
                "danceability":     round(float(avgs_row.danceability), 3),
                "valence":          round(float(avgs_row.valence), 3),
                "acousticness":     round(float(avgs_row.acousticness), 3),
                "instrumentalness": round(float(avgs_row.instrumentalness), 3),
                "tempo":            round(float(avgs_row.tempo), 1),
            }
            audio_profile = {"songs_with_features": avgs_row.n, **avgs, "personality": _compute_personality(avgs)}

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

    album_status_q = db.query(models.UserAlbumStatus.album_id).filter_by(user_id=uid)
    if cutoff:
        album_status_q = album_status_q.filter(models.UserAlbumStatus.created_at >= cutoff)
    album_review_q = db.query(models.Review.album_id).filter(
        models.Review.user_id == uid, models.Review.album_id.isnot(None))
    if cutoff:
        album_review_q = album_review_q.filter(models.Review.created_at >= cutoff)
    albums_listened = len({r[0] for r in album_status_q.all()} | {r[0] for r in album_review_q.all()})

    song_status_q = db.query(models.UserSongStatus.song_id).filter_by(user_id=uid)
    if cutoff:
        song_status_q = song_status_q.filter(models.UserSongStatus.created_at >= cutoff)
    song_review_q = db.query(models.Review.song_id).filter(
        models.Review.user_id == uid, models.Review.song_id.isnot(None))
    if cutoff:
        song_review_q = song_review_q.filter(models.Review.created_at >= cutoff)
    songs_listened = len({r[0] for r in song_status_q.all()} | {r[0] for r in song_review_q.all()})

    # Reviews in period — eager-load relationships used below
    rev_q = (
        db.query(models.Review)
        .options(
            joinedload(models.Review.song).joinedload(models.Song.artist),
            joinedload(models.Review.album).joinedload(models.Album.artist),
        )
        .filter(models.Review.user_id == uid)
    )
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

    # Top genres from listened albums in period — batch query, no loop
    listened_aid_q = db.query(models.UserAlbumStatus.album_id).filter_by(user_id=uid, status="listened")
    if cutoff:
        listened_aid_q = listened_aid_q.filter(models.UserAlbumStatus.created_at >= cutoff)
    listened_aids = [row[0] for row in listened_aid_q.all()]
    genre_counts: dict[str, int] = {}
    if listened_aids:
        for album in (
            db.query(models.Album)
            .options(selectinload(models.Album.genres))
            .filter(models.Album.id.in_(listened_aids))
            .all()
        ):
            for g in album.genres:
                genre_counts[g.name] = genre_counts.get(g.name, 0) + 1
    top_genres = [
        {"name": n, "count": c}
        for n, c in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Audio profile from listened songs — SQL AVG, no Python aggregation
    listened_sid_q = db.query(models.UserSongStatus.song_id).filter_by(user_id=uid, status="listened")
    if cutoff:
        listened_sid_q = listened_sid_q.filter(models.UserSongStatus.created_at >= cutoff)
    listened_sids = [row[0] for row in listened_sid_q.all()]
    audio_profile = None
    if listened_sids:
        avgs_row = (
            db.query(
                func.avg(models.Song.energy).label("energy"),
                func.avg(models.Song.danceability).label("danceability"),
                func.avg(models.Song.valence).label("valence"),
                func.avg(models.Song.acousticness).label("acousticness"),
                func.avg(models.Song.instrumentalness).label("instrumentalness"),
                func.count(models.Song.id).label("n"),
            )
            .filter(models.Song.id.in_(listened_sids), models.Song.energy.isnot(None))
            .one()
        )
        if avgs_row.n:
            avgs = {
                "energy":           round(float(avgs_row.energy), 3),
                "danceability":     round(float(avgs_row.danceability), 3),
                "valence":          round(float(avgs_row.valence), 3),
                "acousticness":     round(float(avgs_row.acousticness), 3),
                "instrumentalness": round(float(avgs_row.instrumentalness), 3),
            }
            audio_profile = {"songs_with_features": avgs_row.n, **avgs, "personality": _compute_personality(avgs)}

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
