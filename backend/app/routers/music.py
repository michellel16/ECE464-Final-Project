from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user
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


# ── Genres ───────────────────────────────────────────────────────────────────

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    return db.query(models.Genre).all()


# ── Artists ───────────────────────────────────────────────────────────────────

@router.get("/artists")
async def list_artists(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    artists = db.query(models.Artist).offset(skip).limit(limit).all()
    await _enrich_missing_images(db, artists, [])
    return [
        {
            "id": a.id, "name": a.name, "bio": a.bio,
            "image_url": a.image_url, "formed_year": a.formed_year,
            "country": a.country,
            "genres": [{"id": g.id, "name": g.name} for g in a.genres],
            "album_count": len(a.albums),
        }
        for a in artists
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
async def get_artist_albums(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    await _enrich_missing_images(db, [], artist.albums)
    return [
        {
            "id": al.id, "title": al.title, "artist_id": al.artist_id,
            "release_date": al.release_date, "cover_url": al.cover_url,
            "description": al.description,
            "genres": [{"id": g.id, "name": g.name} for g in al.genres],
            "average_rating": _avg_rating(db, album_id=al.id),
            "review_count": _review_count(db, album_id=al.id),
            "song_count": len(al.songs),
        }
        for al in artist.albums
    ]


# ── Albums ────────────────────────────────────────────────────────────────────

@router.get("/albums")
async def list_albums(skip: int = 0, limit: int = 30, db: Session = Depends(get_db)):
    albums = db.query(models.Album).offset(skip).limit(limit).all()
    artists = list({al.artist for al in albums if al.artist})
    await _enrich_missing_images(db, artists, albums)
    return [
        {
            "id": al.id, "title": al.title, "artist_id": al.artist_id,
            "artist": {"id": al.artist.id, "name": al.artist.name, "image_url": al.artist.image_url},
            "release_date": al.release_date, "cover_url": al.cover_url,
            "description": al.description,
            "genres": [{"id": g.id, "name": g.name} for g in al.genres],
            "average_rating": _avg_rating(db, album_id=al.id),
            "review_count": _review_count(db, album_id=al.id),
        }
        for al in albums
    ]


@router.get("/albums/{album_id}")
async def get_album(album_id: int, db: Session = Depends(get_db)):
    al = db.query(models.Album).filter(models.Album.id == album_id).first()
    if not al:
        raise HTTPException(status_code=404, detail="Album not found")
    await _enrich_missing_images(db, [al.artist] if al.artist else [], [al])
    return {
        "id": al.id, "title": al.title, "artist_id": al.artist_id,
        "artist": {"id": al.artist.id, "name": al.artist.name, "image_url": al.artist.image_url},
        "release_date": al.release_date, "cover_url": al.cover_url,
        "description": al.description,
        "genres": [{"id": g.id, "name": g.name} for g in al.genres],
        "songs": [
            {
                "id": s.id, "title": s.title,
                "track_number": s.track_number, "duration_seconds": s.duration_seconds,
                "average_rating": _avg_rating(db, song_id=s.id),
                "spotify_id": s.spotify_id,
                "spotify_preview_url": s.spotify_preview_url,
            }
            for s in al.songs
        ],
        "average_rating": _avg_rating(db, album_id=al.id),
        "review_count": _review_count(db, album_id=al.id),
    }


# ── Songs ─────────────────────────────────────────────────────────────────────

@router.get("/songs")
def list_songs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    songs = db.query(models.Song).offset(skip).limit(limit).all()
    return [
        {
            "id": s.id, "title": s.title, "artist_id": s.artist_id,
            "artist": {"id": s.artist.id, "name": s.artist.name},
            "album_id": s.album_id,
            "album": {"id": s.album.id, "title": s.album.title, "cover_url": s.album.cover_url} if s.album else None,
            "duration_seconds": s.duration_seconds, "track_number": s.track_number,
            "average_rating": _avg_rating(db, song_id=s.id),
        }
        for s in songs
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

def _review_row(r: models.Review) -> dict:
    return {
        "id": r.id, "user_id": r.user_id, "username": r.user.username,
        "avatar_url": r.user.avatar_url,
        "song_id": r.song_id, "album_id": r.album_id,
        "text": r.text, "rating": r.rating, "created_at": r.created_at,
    }


@router.get("/albums/{album_id}/reviews")
def get_album_reviews(album_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Review)
        .filter(models.Review.album_id == album_id)
        .order_by(models.Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return [_review_row(r) for r in rows]


@router.post("/albums/{album_id}/reviews", status_code=201)
def create_album_review(
    album_id: int,
    review: schemas.ReviewCreate,
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
    return _review_row(r)


@router.get("/songs/{song_id}/reviews")
def get_song_reviews(song_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Review)
        .filter(models.Review.song_id == song_id)
        .order_by(models.Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return [_review_row(r) for r in rows]


@router.post("/songs/{song_id}/reviews", status_code=201)
def create_song_review(
    song_id: int,
    review: schemas.ReviewCreate,
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
