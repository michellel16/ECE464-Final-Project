from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
def search(q: str, db: Session = Depends(get_db)):
    like = f"%{q}%"

    artists = db.query(models.Artist).filter(models.Artist.name.ilike(like)).limit(5).all()
    albums  = db.query(models.Album).filter(models.Album.title.ilike(like)).limit(8).all()
    songs   = db.query(models.Song).filter(models.Song.title.ilike(like)).limit(8).all()
    users   = db.query(models.User).filter(models.User.username.ilike(like)).limit(5).all()

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
    }
