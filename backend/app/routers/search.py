import asyncio

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from .spotify import _get_client_token

router = APIRouter(prefix="/api/search", tags=["search"])


def _sp_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _needs_image(url: str | None) -> bool:
    """Return True if the URL is absent or a Wikipedia hotlink that may not load."""
    if not url:
        return True
    return "wikimedia.org" in url or "wikipedia.org" in url


async def _enrich_missing_images(db: Session, artists: list, albums: list) -> None:
    """
    For any artist/album missing a reliable image/cover (null or Wikipedia URL),
    fetch it from Spotify using client-credentials and persist to DB.
    Runs all requests in parallel; silently ignores Spotify errors.
    """
    artists_todo = [a for a in artists if _needs_image(a.image_url)]
    albums_todo  = [al for al in albums if _needs_image(al.cover_url)]
    if not artists_todo and not albums_todo:
        return

    try:
        token = await _get_client_token()
    except Exception:
        return  # Spotify not configured — skip enrichment

    headers = _sp_headers(token)

    async def enrich_artist(artist: models.Artist, client: httpx.AsyncClient) -> None:
        try:
            if artist.spotify_id:
                r = await client.get(
                    f"https://api.spotify.com/v1/artists/{artist.spotify_id}",
                    headers=headers,
                )
                if r.status_code == 200:
                    images = r.json().get("images") or []
                    if images:
                        artist.image_url = images[0]["url"]
            else:
                r = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": artist.name, "type": "artist", "limit": 1},
                    headers=headers,
                )
                if r.status_code == 200:
                    items = r.json().get("artists", {}).get("items") or []
                    if items:
                        sp = items[0]
                        images = sp.get("images") or []
                        if images:
                            artist.image_url = images[0]["url"]
                        if not artist.spotify_id and sp.get("id"):
                            artist.spotify_id = sp["id"]
        except Exception:
            pass

    async def enrich_album(album: models.Album, client: httpx.AsyncClient) -> None:
        try:
            if album.spotify_id:
                r = await client.get(
                    f"https://api.spotify.com/v1/albums/{album.spotify_id}",
                    headers=headers,
                )
                if r.status_code == 200:
                    images = r.json().get("images") or []
                    if images:
                        album.cover_url = images[0]["url"]
            else:
                artist_name = album.artist.name if album.artist else ""
                query = f"{album.title} {artist_name}".strip()
                r = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": query, "type": "album", "limit": 1},
                    headers=headers,
                )
                if r.status_code == 200:
                    items = r.json().get("albums", {}).get("items") or []
                    if items:
                        sp = items[0]
                        images = sp.get("images") or []
                        if images:
                            album.cover_url = images[0]["url"]
                        if not album.spotify_id and sp.get("id"):
                            album.spotify_id = sp["id"]
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await asyncio.gather(
                *[enrich_artist(a, client) for a in artists_todo],
                *[enrich_album(al, client) for al in albums_todo],
            )
        db.commit()
    except Exception:
        pass


@router.get("/")
async def search(q: str, db: Session = Depends(get_db)):
    like = f"%{q}%"

    artists = db.query(models.Artist).filter(models.Artist.name.ilike(like)).limit(5).all()
    albums  = db.query(models.Album).filter(models.Album.title.ilike(like)).limit(8).all()
    songs   = db.query(models.Song).filter(models.Song.title.ilike(like)).limit(8).all()
    users   = db.query(models.User).filter(models.User.username.ilike(like)).limit(5).all()

    await _enrich_missing_images(db, artists, albums)

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
