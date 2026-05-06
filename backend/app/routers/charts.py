from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/albums")
def top_albums(
    year: Optional[int] = None,
    decade: Optional[int] = None,
    genre_id: Optional[int] = None,
    limit: int = 25,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            models.Album.id,
            func.avg(models.Review.rating).label("avg_rating"),
            func.count(models.Review.id).label("review_count"),
        )
        .join(models.Review, models.Review.album_id == models.Album.id)
        .group_by(models.Album.id)
        .having(func.count(models.Review.id) >= 1)
    )

    if year:
        q = q.filter(models.Album.release_date.like(f"{year}%"))
    elif decade:
        q = q.filter(
            models.Album.release_date >= str(decade),
            models.Album.release_date < str(decade + 10),
        )

    if genre_id:
        genre_sub = (
            db.query(models.album_genre.c.album_id)
            .filter(models.album_genre.c.genre_id == genre_id)
            .subquery()
        )
        q = q.filter(models.Album.id.in_(genre_sub))

    rows = (
        q.order_by(func.avg(models.Review.rating).desc(), func.count(models.Review.id).desc())
        .offset(skip).limit(limit)
        .all()
    )

    if not rows:
        return []

    album_ids = [r.id for r in rows]
    stats = {r.id: (round(float(r.avg_rating), 2), r.review_count) for r in rows}

    albums = {
        a.id: a for a in (
            db.query(models.Album)
            .options(joinedload(models.Album.artist), joinedload(models.Album.genres))
            .filter(models.Album.id.in_(album_ids))
            .all()
        )
    }

    return [
        {
            "rank": skip + i + 1,
            "album": {
                "id": albums[aid].id, "title": albums[aid].title,
                "cover_url": albums[aid].cover_url,
                "release_date": albums[aid].release_date,
                "artist": {"id": albums[aid].artist.id, "name": albums[aid].artist.name},
                "genres": [{"id": g.id, "name": g.name} for g in albums[aid].genres],
            },
            "average_rating": stats[aid][0],
            "review_count": stats[aid][1],
        }
        for i, aid in enumerate(album_ids)
        if aid in albums
    ]


@router.get("/genres")
def chart_genres(db: Session = Depends(get_db)):
    genres = db.query(models.Genre).order_by(models.Genre.name).all()
    return [{"id": g.id, "name": g.name} for g in genres]


@router.get("/years")
def chart_years(db: Session = Depends(get_db)):
    dates = (
        db.query(models.Album.release_date)
        .filter(models.Album.release_date.isnot(None))
        .all()
    )
    years = sorted(
        {int(d[0][:4]) for d in dates if d[0] and len(d[0]) >= 4 and d[0][:4].isdigit()},
        reverse=True,
    )
    return years
