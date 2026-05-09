import asyncio
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .. import models
from ..database import get_db, SessionLocal
from ..auth import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/spotify", tags=["spotify"])

SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/api/spotify/callback")
SPOTIFY_SCOPES        = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"
FRONTEND_URL          = os.getenv("FRONTEND_URL", "http://localhost:5173")

_STATE_EXPIRE_MINUTES = 10

# ── MusicBrainz background-job state ─────────────────────────────────────────

_mb_progress: dict = {
    "running":      False,
    "done":         0,
    "total":        0,
    "genres_added": 0,
}

# ── Client-credentials token cache (app-level, no user needed) ──────────────

_cc_cache: dict = {"token": None, "expires_at": datetime.min}


async def _get_client_token() -> str:
    """Get a Spotify client-credentials token, refreshing only when expired."""
    global _cc_cache
    if _cc_cache["token"] and datetime.utcnow() < _cc_cache["expires_at"]:
        return _cc_cache["token"]
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Spotify credentials not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            )
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Spotify unavailable")
    if resp.status_code != 200:
        raise HTTPException(status_code=503, detail="Spotify client auth failed")
    data = resp.json()
    _cc_cache["token"] = data["access_token"]
    _cc_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600) - 30)
    return _cc_cache["token"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_state(user_id: int) -> str:
    """Sign a short-lived JWT to use as OAuth state (CSRF protection + carries user_id)."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=_STATE_EXPIRE_MINUTES),
        "typ": "spotify_state",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_state(state: str) -> int:
    """Decode the state JWT and return user_id, or raise 400."""
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "spotify_state":
            raise ValueError
        return int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")


async def _get_valid_token(user: models.User, db: Session) -> str:
    """Return a valid Spotify access token, refreshing if needed."""
    if not user.spotify_access_token:
        raise HTTPException(status_code=401, detail="Spotify account not connected")

    if user.spotify_token_expires_at and datetime.utcnow() >= user.spotify_token_expires_at:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type":    "refresh_token",
                    "refresh_token": user.spotify_refresh_token,
                    "client_id":     SPOTIFY_CLIENT_ID,
                    "client_secret": SPOTIFY_CLIENT_SECRET,
                },
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Spotify token refresh failed — please reconnect")
        data = resp.json()
        user.spotify_access_token = data["access_token"]
        user.spotify_token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
        if "refresh_token" in data:
            user.spotify_refresh_token = data["refresh_token"]
        db.commit()

    return user.spotify_access_token


def _spotify_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _sync_artist_genres(artist, spotify_genres: list[str], db) -> None:
    """
    Map Spotify genre strings onto Genre rows and attach them to the artist.
    Spotify uses lowercase slugs ("dance pop"); we title-case them to match
    seed data ("Dance Pop"). Skips genres already linked.
    """
    existing_ids = {g.id for g in artist.genres}
    for raw in spotify_genres[:5]:
        name = raw.title()  # "dance pop" → "Dance Pop"
        genre = (
            db.query(models.Genre).filter(models.Genre.name == name).first()
            or db.query(models.Genre).filter(models.Genre.name.ilike(raw)).first()
        )
        if not genre:
            genre = models.Genre(name=name)
            db.add(genre)
            db.flush()
        if genre.id not in existing_ids:
            artist.genres.append(genre)
            existing_ids.add(genre.id)


def _sync_album_genres(album, artist, db) -> None:
    """Propagate the artist's genres onto the album when the album has none."""
    if album.genres or not artist.genres:
        return
    existing_ids = {g.id for g in album.genres}
    for genre in artist.genres:
        if genre.id not in existing_ids:
            album.genres.append(genre)
            existing_ids.add(genre.id)


def _compute_personality(avg: dict) -> str:
    """Derive a human-readable music personality from average audio features."""
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


# ── OAuth endpoints ───────────────────────────────────────────────────────────

@router.get("/auth-url")
async def get_auth_url(current_user: models.User = Depends(get_current_user)):
    """Return the Spotify authorization URL for the frontend to redirect to."""
    if not SPOTIFY_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Spotify integration not configured")

    state = _make_state(current_user.id)
    params = urlencode({
        "client_id":     SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri":  SPOTIFY_REDIRECT_URI,
        "scope":         SPOTIFY_SCOPES,
        "state":         state,
        "show_dialog":   "true",
    })
    return {"url": f"https://accounts.spotify.com/authorize?{params}"}


@router.get("/callback")
async def spotify_callback(
    code: str  = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db),
):
    """Handle Spotify OAuth callback — exchange code for tokens, store them, redirect to frontend."""

    # Decode state first so we can always redirect to the user's own profile page.
    # Fall back to home if state is missing or invalid.
    profile_url = FRONTEND_URL  # fallback
    user = None
    if state:
        try:
            user_id = _decode_state(state)
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                profile_url = f"{FRONTEND_URL}/users/{user.username}"
        except Exception:
            pass

    def _err(reason: str):
        print(f"[Spotify callback error] {reason}")
        return RedirectResponse(f"{profile_url}?spotify=error&reason={reason}")

    if error:
        return _err(error)

    if not code or not state:
        return _err("missing_params")

    if not user:
        return _err("user_not_found")

    # Exchange authorization code for tokens
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  SPOTIFY_REDIRECT_URI,
                "client_id":     SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
        )
    if token_resp.status_code != 200:
        print(f"[Spotify token exchange failed] {token_resp.status_code}: {token_resp.text}")
        return _err("token_exchange_failed")

    token_data = token_resp.json()
    access_token  = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in    = token_data.get("expires_in", 3600)

    # Fetch Spotify user profile
    async with httpx.AsyncClient(timeout=10.0) as client:
        profile_resp = await client.get(
            "https://api.spotify.com/v1/me",
            headers=_spotify_headers(access_token),
        )
    if profile_resp.status_code != 200:
        return _err("profile_fetch_failed")

    sp_profile = profile_resp.json()

    # Store everything
    user.spotify_id               = sp_profile.get("id")
    user.spotify_access_token     = access_token
    user.spotify_refresh_token    = refresh_token
    user.spotify_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    user.spotify_display_name     = sp_profile.get("display_name")
    images = sp_profile.get("images", [])
    user.spotify_image_url        = images[0]["url"] if images else None
    db.commit()

    return RedirectResponse(f"{FRONTEND_URL}/users/{user.username}?spotify=connected")


@router.get("/status")
async def spotify_status(current_user: models.User = Depends(get_current_user)):
    """Return whether the current user has a connected Spotify account."""
    return {
        "connected":      bool(current_user.spotify_access_token),
        "spotify_id":     current_user.spotify_id,
        "display_name":   current_user.spotify_display_name,
        "image_url":      current_user.spotify_image_url,
    }


@router.delete("/disconnect")
async def spotify_disconnect(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove Spotify tokens from the user's account."""
    current_user.spotify_id               = None
    current_user.spotify_access_token     = None
    current_user.spotify_refresh_token    = None
    current_user.spotify_token_expires_at = None
    current_user.spotify_display_name     = None
    current_user.spotify_image_url        = None
    db.commit()
    return {"connected": False}


# ── Spotify data endpoints ────────────────────────────────────────────────────

@router.get("/me")
async def spotify_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the current user's Spotify profile."""
    token = await _get_valid_token(current_user, db)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("https://api.spotify.com/v1/me", headers=_spotify_headers(token))
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch Spotify profile")
    return resp.json()


@router.get("/playlists")
async def spotify_playlists(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the current user's Spotify playlists."""
    token = await _get_valid_token(current_user, db)
    playlists = []
    url = "https://api.spotify.com/v1/me/playlists?limit=50"
    async with httpx.AsyncClient(timeout=10.0) as client:
        while url:
            resp = await client.get(url, headers=_spotify_headers(token))
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch playlists")
            data = resp.json()
            for p in data.get("items", []):
                if not p or not p.get("id"):
                    continue
                owner = p.get("owner") or {}
                # Only include playlists the user created themselves
                if owner.get("id") != current_user.spotify_id:
                    continue
                images = p.get("images") or []
                tracks_obj = p.get("tracks") or {}
                playlists.append({
                    "id":          p["id"],
                    "name":        p.get("name", "Untitled"),
                    "track_count": tracks_obj.get("total", 0),
                    "image_url":   images[0]["url"] if images else None,
                })
            url = data.get("next")
    return playlists


@router.get("/playlists/{playlist_id}/tracks")
async def spotify_playlist_tracks(
    playlist_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch tracks from a Spotify playlist, annotating which ones are already in Tunelog."""
    token = await _get_valid_token(current_user, db)
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items?limit=100"

    async with httpx.AsyncClient(timeout=10.0) as client:
        while url:
            resp = await client.get(url, headers=_spotify_headers(token))
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Spotify returned {resp.status_code}: {resp.text[:200]}"
                )
            data = resp.json()
            for item in data.get("items", []):
                track = item.get("item") or item.get("track")
                if not track or not track.get("id") or track.get("type") != "track":
                    continue
                artists = track.get("artists", [])
                album   = track.get("album", {})
                images  = album.get("images") or []
                tracks.append({
                    "spotify_id":   track["id"],
                    "name":         track["name"],
                    "artist_name":  artists[0]["name"] if artists else "Unknown",
                    "artist_spotify_id": artists[0]["id"] if artists else None,
                    "album_name":   album.get("name"),
                    "album_spotify_id": album.get("id"),
                    "cover_url":    images[0]["url"] if images else None,
                    "duration_ms":  track.get("duration_ms"),
                    "preview_url":  track.get("preview_url"),
                })
            url = data.get("next")

    # Annotate which tracks already exist in Tunelog
    spotify_ids = [t["spotify_id"] for t in tracks]
    existing = (
        db.query(models.Song.spotify_id, models.Song.id)
        .filter(models.Song.spotify_id.in_(spotify_ids))
        .all()
    )
    existing_map = {row[0]: row[1] for row in existing}
    for t in tracks:
        t["tunelog_song_id"] = existing_map.get(t["spotify_id"])

    return tracks


@router.post("/import-playlist-as-list")
async def import_playlist_as_list(
    body: dict = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Tunelog list from a Spotify playlist, linking any tracks already in Tunelog."""
    playlist_id = body.get("playlist_id")
    if not playlist_id:
        raise HTTPException(status_code=400, detail="playlist_id is required")

    token = await _get_valid_token(current_user, db)

    async with httpx.AsyncClient(timeout=15.0) as client:
        meta_resp = await client.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}?fields=name,description,images",
            headers=_spotify_headers(token),
        )
        if meta_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch playlist from Spotify")
        meta = meta_resp.json()

        tracks_data = []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items?limit=100"
        while url:
            resp = await client.get(url, headers=_spotify_headers(token))
            if resp.status_code != 200:
                break
            data = resp.json()
            for item in data.get("items", []):
                track = item.get("item") or item.get("track")
                if track and track.get("id") and track.get("type") == "track":
                    tracks_data.append(track["id"])
            url = data.get("next")

    # Match tracks already imported into Tunelog by spotify_id
    matched_songs = (
        db.query(models.Song)
        .filter(models.Song.spotify_id.in_(tracks_data))
        .all()
    ) if tracks_data else []
    song_order = {sid: i for i, sid in enumerate(tracks_data)}
    matched_songs.sort(key=lambda s: song_order.get(s.spotify_id, 9999))

    images = meta.get("images") or []
    list_obj = models.List(
        user_id=current_user.id,
        name=meta.get("name", "Spotify Playlist"),
        description=(meta.get("description") or "").strip() or f"Imported from Spotify",
        list_type="custom",
        is_public=True,
        cover_url=images[0]["url"] if images else None,
    )
    db.add(list_obj)
    db.flush()

    for song in matched_songs:
        db.add(models.ListItem(list_id=list_obj.id, song_id=song.id))

    db.commit()
    return {
        "list_id":      list_obj.id,
        "list_name":    list_obj.name,
        "tracks_total": len(tracks_data),
        "tracks_added": len(matched_songs),
    }


@router.post("/import-track")
async def import_track(
    body: dict = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import a Spotify track into Tunelog as a Song.
    Body: { spotify_track_id: str }
    Returns the Tunelog song id.
    """
    spotify_track_id = body.get("spotify_track_id")
    if not spotify_track_id:
        raise HTTPException(status_code=400, detail="spotify_track_id is required")

    # Return existing song if already imported
    existing = db.query(models.Song).filter(models.Song.spotify_id == spotify_track_id).first()
    if existing:
        return {"song_id": existing.id, "already_existed": True}

    token = await _get_valid_token(current_user, db)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Fetch track metadata
        track_resp = await client.get(
            f"https://api.spotify.com/v1/tracks/{spotify_track_id}",
            headers=_spotify_headers(token),
        )
        if track_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch track from Spotify")
        track = track_resp.json()

        # Try to fetch audio features (may return 403 for new Spotify apps)
        features_resp = await client.get(
            f"https://api.spotify.com/v1/audio-features/{spotify_track_id}",
            headers=_spotify_headers(token),
        )
        features = features_resp.json() if features_resp.status_code == 200 else {}

        # Resolve artist — update existing artists' missing fields
        sp_artists = track.get("artists", [])
        sp_artist  = sp_artists[0] if sp_artists else {}
        artist = db.query(models.Artist).filter(models.Artist.spotify_id == sp_artist.get("id")).first()
        if not artist and sp_artist.get("name"):
            artist = db.query(models.Artist).filter(
                models.Artist.name.ilike(sp_artist["name"])
            ).first()

        # Fetch full artist from Spotify if we need image or genres
        sp_artist_full = None
        if sp_artist.get("id") and (not artist or not artist.image_url or not artist.genres):
            art_resp = await client.get(
                f"https://api.spotify.com/v1/artists/{sp_artist['id']}",
                headers=_spotify_headers(token),
            )
            if art_resp.status_code == 200:
                sp_artist_full = art_resp.json()

        if artist:
            # Fill in any missing fields on the existing artist
            if not artist.spotify_id and sp_artist.get("id"):
                artist.spotify_id = sp_artist["id"]
            if not artist.image_url and sp_artist_full:
                images = sp_artist_full.get("images") or []
                if images:
                    artist.image_url = images[0]["url"]
        else:
            artist = models.Artist(
                name=sp_artist.get("name", "Unknown Artist"),
                spotify_id=sp_artist.get("id"),
                image_url=(sp_artist_full.get("images") or [{}])[0].get("url") if sp_artist_full else None,
            )
            db.add(artist)
            db.flush()

    if sp_artist_full:
        _sync_artist_genres(artist, sp_artist_full.get("genres", []), db)

    # Resolve album
    sp_album = track.get("album", {})
    album = db.query(models.Album).filter(models.Album.spotify_id == sp_album.get("id")).first()
    if not album and sp_album.get("name"):
        album = db.query(models.Album).filter(
            models.Album.title.ilike(sp_album["name"]),
            models.Album.artist_id == artist.id,
        ).first()
    sp_images = sp_album.get("images") or []
    if album:
        # Fill in any missing fields on the existing album
        if not album.spotify_id and sp_album.get("id"):
            album.spotify_id = sp_album["id"]
        if not album.cover_url and sp_images:
            album.cover_url = sp_images[0]["url"]
        if not album.release_date and sp_album.get("release_date"):
            album.release_date = sp_album["release_date"][:4]
    elif sp_album.get("name"):
        release_date = sp_album.get("release_date")
        album = models.Album(
            title=sp_album["name"],
            artist_id=artist.id,
            spotify_id=sp_album.get("id"),
            cover_url=sp_images[0]["url"] if sp_images else None,
            release_date=release_date[:4] if release_date else None,
        )
        db.add(album)
        db.flush()

    if album:
        _sync_album_genres(album, artist, db)

    # Create song
    duration_ms = track.get("duration_ms")
    song = models.Song(
        title=track["name"],
        artist_id=artist.id,
        album_id=album.id if album else None,
        duration_seconds=int(duration_ms / 1000) if duration_ms else None,
        track_number=track.get("track_number"),
        spotify_id=spotify_track_id,
        spotify_preview_url=track.get("preview_url"),
        danceability=features.get("danceability"),
        energy=features.get("energy"),
        valence=features.get("valence"),
        loudness=features.get("loudness"),
        tempo=features.get("tempo"),
        acousticness=features.get("acousticness"),
        instrumentalness=features.get("instrumentalness"),
    )
    db.add(song)
    db.commit()
    db.refresh(song)

    # Fire-and-forget: embed the new song (and its artist/album) in the background
    from ..embeddings import reembed_song_bg, reembed_artist_bg, reembed_album_bg
    asyncio.create_task(reembed_song_bg(song.id))
    asyncio.create_task(reembed_artist_bg(artist.id))
    if album:
        asyncio.create_task(reembed_album_bg(album.id))

    return {"song_id": song.id, "already_existed": False}


@router.get("/audio-features/{song_id}")
async def refresh_audio_features(
    song_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-fetch audio features from Spotify for a Tunelog song that has a spotify_id."""
    song = db.query(models.Song).filter(models.Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    if not song.spotify_id:
        raise HTTPException(status_code=400, detail="Song has no Spotify ID")

    token = await _get_valid_token(current_user, db)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"https://api.spotify.com/v1/audio-features/{song.spotify_id}",
            headers=_spotify_headers(token),
        )
    if resp.status_code == 403:
        raise HTTPException(status_code=403, detail="Audio features unavailable (Spotify API restriction for new apps)")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch audio features")

    f = resp.json()
    song.danceability     = f.get("danceability")
    song.energy           = f.get("energy")
    song.valence          = f.get("valence")
    song.loudness         = f.get("loudness")
    song.tempo            = f.get("tempo")
    song.acousticness     = f.get("acousticness")
    song.instrumentalness = f.get("instrumentalness")
    db.commit()

    return {
        "danceability":     song.danceability,
        "energy":           song.energy,
        "valence":          song.valence,
        "loudness":         song.loudness,
        "tempo":            song.tempo,
        "acousticness":     song.acousticness,
        "instrumentalness": song.instrumentalness,
    }


@router.get("/stats/audio-profile")
async def audio_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute average audio features for songs the user has listened to
    that have Spotify feature data.
    """
    listened_song_ids = [
        row[0] for row in
        db.query(models.UserSongStatus.song_id)
        .filter_by(user_id=current_user.id, status="listened")
        .all()
    ]
    if not listened_song_ids:
        return {"songs_with_features": 0, "personality": None}

    songs = (
        db.query(models.Song)
        .filter(
            models.Song.id.in_(listened_song_ids),
            models.Song.energy.isnot(None),
        )
        .all()
    )

    if not songs:
        return {"songs_with_features": 0, "personality": None}

    n = len(songs)
    avgs = {
        "energy":           sum(s.energy           or 0 for s in songs) / n,
        "danceability":     sum(s.danceability     or 0 for s in songs) / n,
        "valence":          sum(s.valence          or 0 for s in songs) / n,
        "acousticness":     sum(s.acousticness     or 0 for s in songs) / n,
        "instrumentalness": sum(s.instrumentalness or 0 for s in songs) / n,
        "tempo":            sum(s.tempo            or 0 for s in songs) / n,
    }

    return {
        "songs_with_features": n,
        "personality":         _compute_personality(avgs),
        **{k: round(v, 3) for k, v in avgs.items()},
    }


# ── MusicBrainz helpers ───────────────────────────────────────────────────────

_MB_HEADERS = {
    "User-Agent": "Tunelog/1.0 (music-catalog-app)",
    "Accept":     "application/json",
}


async def _musicbrainz_backfill(artist_ids: list[int]) -> None:
    """
    Background task: tag untagged artists via MusicBrainz then propagate to albums.
    Two requests per matched artist (search → lookup with inc=tags+genres).
    Uses direct SQL inserts on association tables to avoid ORM collection issues.
    Rate-limited to 1 req/sec per MusicBrainz policy (sleep after every HTTP request).
    """
    global _mb_progress
    _mb_progress["running"]      = True
    _mb_progress["done"]         = 0
    _mb_progress["total"]        = len(artist_ids)
    _mb_progress["genres_added"] = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for artist_id in artist_ids:
            db = SessionLocal()
            try:
                # Re-check in a fresh session — a previous iteration may have tagged this artist
                already_tagged = db.execute(
                    models.artist_genre.select()
                    .where(models.artist_genre.c.artist_id == artist_id)
                ).first()
                if already_tagged:
                    continue

                artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
                if not artist:
                    continue

                # Step 1: search MusicBrainz for MBID
                search_resp = await client.get(
                    "https://musicbrainz.org/ws/2/artist",
                    params={"query": f'artist:"{artist.name}"', "limit": 1, "fmt": "json"},
                    headers=_MB_HEADERS,
                )
                await asyncio.sleep(1.1)

                if search_resp.status_code != 200:
                    continue

                items = search_resp.json().get("artists") or []
                if not items:
                    continue

                mb_artist = items[0]
                mb_name = mb_artist.get("name", "").lower()
                db_name = artist.name.lower()
                score   = int(mb_artist.get("score", 0) or 0)
                # Accept exact name match OR score-100 result (handles minor variants)
                if mb_name != db_name and score < 100:
                    continue

                mbid = mb_artist.get("id")
                if not mbid:
                    continue

                # Step 2: full lookup with tags + genres
                lookup_resp = await client.get(
                    f"https://musicbrainz.org/ws/2/artist/{mbid}",
                    params={"inc": "tags+genres", "fmt": "json"},
                    headers=_MB_HEADERS,
                )
                await asyncio.sleep(1.1)

                if lookup_resp.status_code != 200:
                    continue

                mb_full = lookup_resp.json()
                # Prefer curated MusicBrainz genres; fall back to free-form tags
                raw = (
                    [g["name"] for g in (mb_full.get("genres") or []) if g.get("count", 0) > 0]
                    or [t["name"] for t in (mb_full.get("tags") or []) if t.get("count", 0) > 0]
                )
                if not raw:
                    continue

                # Resolve/create Genre rows
                genre_ids: list[int] = []
                for tag in raw[:5]:
                    name = tag.title()
                    genre = (
                        db.query(models.Genre).filter(models.Genre.name == name).first()
                        or db.query(models.Genre).filter(models.Genre.name.ilike(tag)).first()
                    )
                    if not genre:
                        genre = models.Genre(name=name)
                        db.add(genre)
                        db.flush()
                    genre_ids.append(genre.id)

                if not genre_ids:
                    continue

                # Insert artist→genre associations (skip duplicates)
                for gid in genre_ids:
                    db.execute(
                        pg_insert(models.artist_genre)
                        .values(artist_id=artist_id, genre_id=gid)
                        .on_conflict_do_nothing()
                    )

                # Propagate to all albums — on_conflict_do_nothing skips duplicates
                album_ids = [
                    row[0] for row in
                    db.query(models.Album.id)
                    .filter(models.Album.artist_id == artist_id)
                    .all()
                ]
                for aid in album_ids:
                    for gid in genre_ids:
                        db.execute(
                            pg_insert(models.album_genre)
                            .values(album_id=aid, genre_id=gid)
                            .on_conflict_do_nothing()
                        )

                db.commit()
                _mb_progress["genres_added"] += 1

            except Exception as e:
                print(f"[MusicBrainz] Error for artist {artist_id}: {e}")
                try:
                    db.rollback()
                except Exception:
                    pass
            finally:
                db.close()
                _mb_progress["done"] += 1

    _mb_progress["running"] = False


# ── Metadata backfill ────────────────────────────────────────────────────────

@router.get("/backfill-status")
async def backfill_status():
    """Return current MusicBrainz background-job progress."""
    return dict(_mb_progress)


@router.post("/backfill-metadata")
async def backfill_metadata(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    One-time backfill: for every artist/album already in the DB that is missing
    genres or release_date, fetch the data from Spotify and persist it.
    Uses client-credentials (no user scopes required).
    """
    stats = {
        "artists_genres_synced": 0,
        "albums_genres_propagated": 0,
        "albums_release_date_fixed": 0,
        "spotify_available": False,
        "still_untagged_albums": 0,
    }

    # Try to get a client-credentials token; Spotify steps are skipped if unavailable
    token: str | None = None
    try:
        token = await _get_client_token()
        stats["spotify_available"] = True
    except HTTPException:
        pass

    # ── 1a. Artists WITH spotify_id but no genres — batch lookup ─────────────
    all_artists = (
        db.query(models.Artist)
        .options(joinedload(models.Artist.genres))
        .all()
    )
    artists_with_id    = [a for a in all_artists if not a.genres and a.spotify_id]
    artists_without_id = [a for a in all_artists if not a.genres and not a.spotify_id]

    if artists_with_id and token:
        sp_artist_data: dict[str, dict] = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(0, len(artists_with_id), 50):
                batch = ",".join(a.spotify_id for a in artists_with_id[i:i+50])
                resp = await client.get(
                    "https://api.spotify.com/v1/artists",
                    params={"ids": batch},
                    headers=_spotify_headers(token),
                )
                if resp.status_code == 200:
                    for sp in (resp.json().get("artists") or []):
                        if sp:
                            sp_artist_data[sp["id"]] = sp

        for artist in artists_with_id:
            sp = sp_artist_data.get(artist.spotify_id)
            if not sp:
                continue
            _sync_artist_genres(artist, sp.get("genres", []), db)
            if not artist.image_url:
                imgs = sp.get("images") or []
                if imgs:
                    artist.image_url = imgs[0]["url"]
            if artist.genres:
                stats["artists_genres_synced"] += 1

        db.flush()

    # ── 1b. Artists WITHOUT spotify_id — search Spotify by name ──────────────
    if artists_without_id and token:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for artist in artists_without_id:
                resp = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": f"artist:{artist.name}", "type": "artist", "limit": 1},
                    headers=_spotify_headers(token),
                )
                if resp.status_code != 200:
                    continue
                items = (resp.json().get("artists") or {}).get("items") or []
                if not items:
                    continue
                sp = items[0]
                # Only accept an exact name match to avoid mis-attribution
                if sp["name"].lower() != artist.name.lower():
                    continue
                artist.spotify_id = sp["id"]
                if not artist.image_url:
                    imgs = sp.get("images") or []
                    if imgs:
                        artist.image_url = imgs[0]["url"]
                _sync_artist_genres(artist, sp.get("genres", []), db)
                if artist.genres:
                    stats["artists_genres_synced"] += 1

        db.flush()

    # ── 2. Propagate artist genres → albums (direct SQL, no Spotify needed) ────
    # Find (album_id, genre_id) pairs where the artist has that genre but the
    # album does not yet. Uses raw SQL to avoid ORM collection-management issues.
    propagate_rows = db.execute(text("""
        SELECT DISTINCT ag.genre_id, alb.id AS album_id
        FROM   artist_genre ag
        JOIN   albums       alb  ON alb.artist_id = ag.artist_id
        WHERE  NOT EXISTS (
            SELECT 1 FROM album_genre ag2
            WHERE  ag2.album_id = alb.id
            AND    ag2.genre_id = ag.genre_id
        )
    """)).fetchall()

    all_albums = db.query(models.Album).options(joinedload(models.Album.genres)).all()

    for row in propagate_rows:
        db.execute(
            pg_insert(models.album_genre)
            .values(album_id=row.album_id, genre_id=row.genre_id)
            .on_conflict_do_nothing()
        )
    stats["albums_genres_propagated"] = len(propagate_rows)

    # ── 3. Albums missing release_date (requires Spotify) ────────────────────
    albums_missing_date = [a for a in all_albums if not a.release_date and a.spotify_id]

    if albums_missing_date and token:
        sp_album_data: dict[str, dict] = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(0, len(albums_missing_date), 20):
                batch = ",".join(a.spotify_id for a in albums_missing_date[i:i+20])
                resp = await client.get(
                    "https://api.spotify.com/v1/albums",
                    params={"ids": batch},
                    headers=_spotify_headers(token),
                )
                if resp.status_code == 200:
                    for sp in (resp.json().get("albums") or []):
                        if sp:
                            sp_album_data[sp["id"]] = sp

        for album in albums_missing_date:
            sp = sp_album_data.get(album.spotify_id)
            if sp and sp.get("release_date"):
                album.release_date = sp["release_date"][:4]
                stats["albums_release_date_fixed"] += 1

    db.commit()

    # Tally remaining untagged counts directly from DB (ORM objects expired after commit)
    stats["still_untagged_albums"] = db.execute(text("""
        SELECT COUNT(*) FROM albums
        WHERE NOT EXISTS (SELECT 1 FROM album_genre WHERE album_genre.album_id = albums.id)
    """)).scalar() or 0

    # ── 4. Launch MusicBrainz background job for remaining untagged artists ───
    untagged_artist_ids = [
        row[0] for row in db.execute(text("""
            SELECT id FROM artists
            WHERE NOT EXISTS (SELECT 1 FROM artist_genre WHERE artist_genre.artist_id = artists.id)
        """)).fetchall()
    ]
    stats["mb_started"]      = False
    stats["mb_artist_queue"] = len(untagged_artist_ids)

    if untagged_artist_ids and not _mb_progress["running"]:
        asyncio.create_task(_musicbrainz_backfill(untagged_artist_ids))
        stats["mb_started"] = True

    return stats


# ── Catalog search (no user auth required) ───────────────────────────────────

@router.get("/search")
async def spotify_catalog_search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Search Spotify's full catalog for tracks, albums, and artists."""
    token = await _get_client_token()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.spotify.com/v1/search",
                params={"q": q, "type": "track,album,artist", "limit": 8},
                headers=_spotify_headers(token),
            )
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="Spotify unavailable")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Spotify search failed")
    raw = resp.json()

    # ── Format tracks ──
    tracks = []
    for t in raw.get("tracks", {}).get("items", []) or []:
        if not t:
            continue
        artists = t.get("artists") or []
        album   = t.get("album") or {}
        images  = album.get("images") or []
        tracks.append({
            "spotify_id":   t["id"],
            "name":         t["name"],
            "artist_name":  artists[0]["name"] if artists else "Unknown",
            "artist_spotify_id": artists[0]["id"] if artists else None,
            "album_name":   album.get("name"),
            "album_spotify_id": album.get("id"),
            "cover_url":    images[0]["url"] if images else None,
            "duration_ms":  t.get("duration_ms"),
            "preview_url":  t.get("preview_url"),
        })

    # ── Format albums ──
    albums = []
    for a in raw.get("albums", {}).get("items", []) or []:
        if not a:
            continue
        artists = a.get("artists") or []
        images  = a.get("images") or []
        albums.append({
            "spotify_id":   a["id"],
            "name":         a["name"],
            "artist_name":  artists[0]["name"] if artists else "Unknown",
            "artist_spotify_id": artists[0]["id"] if artists else None,
            "cover_url":    images[0]["url"] if images else None,
            "release_date": a.get("release_date", "")[:4],
            "track_count":  a.get("total_tracks", 0),
            "album_type":   a.get("album_type", "album"),
        })

    # ── Format artists ──
    artists_out = []
    for a in raw.get("artists", {}).get("items", []) or []:
        if not a:
            continue
        images = a.get("images") or []
        artists_out.append({
            "spotify_id": a["id"],
            "name":       a["name"],
            "image_url":  images[0]["url"] if images else None,
            "genres":     a.get("genres", [])[:3],
            "followers":  a.get("followers", {}).get("total", 0),
        })

    # ── Annotate which are already in Tunelog ──
    track_ids  = [t["spotify_id"] for t in tracks]
    album_ids  = [a["spotify_id"] for a in albums]
    artist_ids = [a["spotify_id"] for a in artists_out]

    existing_songs   = {r[0]: r[1] for r in db.query(models.Song.spotify_id,   models.Song.id  ).filter(models.Song.spotify_id.in_(track_ids)  ).all()}
    existing_albums  = {r[0]: r[1] for r in db.query(models.Album.spotify_id,  models.Album.id ).filter(models.Album.spotify_id.in_(album_ids)  ).all()}
    existing_artists = {r[0]: r[1] for r in db.query(models.Artist.spotify_id, models.Artist.id).filter(models.Artist.spotify_id.in_(artist_ids)).all()}

    for t in tracks:
        t["tunelog_song_id"] = existing_songs.get(t["spotify_id"])
    for a in albums:
        a["tunelog_album_id"] = existing_albums.get(a["spotify_id"])
    for a in artists_out:
        a["tunelog_artist_id"] = existing_artists.get(a["spotify_id"])

    return {"tracks": tracks, "albums": albums, "artists": artists_out}


# ── Album import ──────────────────────────────────────────────────────────────

@router.post("/import-album")
async def import_album(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Import a full Spotify album (artist + album + all tracks + audio features) into Tunelog.
    Body: { spotify_album_id: str }
    """
    spotify_album_id = body.get("spotify_album_id")
    if not spotify_album_id:
        raise HTTPException(status_code=400, detail="spotify_album_id is required")

    existing = db.query(models.Album).filter(models.Album.spotify_id == spotify_album_id).first()
    if existing:
        return {
            "album_id":       existing.id,
            "song_count":     len(existing.songs),
            "already_existed": True,
        }

    token = await _get_client_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Full album (includes tracks with up to 50 items)
        album_resp = await client.get(
            f"https://api.spotify.com/v1/albums/{spotify_album_id}",
            headers=_spotify_headers(token),
        )
        if album_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch album from Spotify")
        sp_album = album_resp.json()

        # Extra pages of tracks if album has > 50 tracks
        tracks_data = sp_album.get("tracks", {})
        sp_tracks   = list(tracks_data.get("items", []) or [])
        next_url    = tracks_data.get("next")
        while next_url:
            page = await client.get(next_url, headers=_spotify_headers(token))
            if page.status_code != 200:
                break
            page_data = page.json()
            sp_tracks.extend(page_data.get("items", []) or [])
            next_url = page_data.get("next")

    # ── Resolve / create artist ──
    sp_artists = sp_album.get("artists") or []
    sp_artist  = sp_artists[0] if sp_artists else {}
    artist = None
    if sp_artist.get("id"):
        artist = db.query(models.Artist).filter(models.Artist.spotify_id == sp_artist["id"]).first()
    if not artist and sp_artist.get("name"):
        artist = db.query(models.Artist).filter(models.Artist.name.ilike(sp_artist["name"])).first()

    # Fetch full artist for image + genres (new artist, or existing one missing either)
    sp_art_full = None
    if sp_artist.get("id") and (not artist or not artist.image_url or not artist.genres):
        async with httpx.AsyncClient(timeout=10.0) as client:
            art_resp = await client.get(
                f"https://api.spotify.com/v1/artists/{sp_artist['id']}",
                headers=_spotify_headers(token),
            )
        if art_resp.status_code == 200:
            sp_art_full = art_resp.json()

    if not artist:
        art_images = (sp_art_full.get("images") or []) if sp_art_full else []
        artist = models.Artist(
            name=(sp_art_full or sp_artist).get("name", "Unknown Artist"),
            spotify_id=sp_artist.get("id"),
            image_url=art_images[0]["url"] if art_images else None,
        )
        db.add(artist)
        db.flush()
    else:
        if not artist.spotify_id and sp_artist.get("id"):
            artist.spotify_id = sp_artist["id"]
        if not artist.image_url and sp_art_full:
            imgs = sp_art_full.get("images") or []
            if imgs:
                artist.image_url = imgs[0]["url"]
        db.flush()

    if sp_art_full:
        _sync_artist_genres(artist, sp_art_full.get("genres", []), db)

    # ── Create album ──
    images       = sp_album.get("images") or []
    release_date = sp_album.get("release_date", "")
    album = models.Album(
        title=sp_album["name"],
        artist_id=artist.id,
        spotify_id=spotify_album_id,
        cover_url=images[0]["url"] if images else None,
        release_date=release_date[:4] if release_date else None,
        description=sp_album.get("label"),
    )
    db.add(album)
    db.flush()
    _sync_album_genres(album, artist, db)

    # ── Fetch audio features in one batch (best-effort) ──
    track_ids = [t["id"] for t in sp_tracks if t and t.get("id")]
    features_map: dict = {}
    if track_ids:
        # Batch endpoint allows up to 100 ids
        async with httpx.AsyncClient(timeout=10.0) as client:
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                feat_resp = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    params={"ids": ",".join(batch)},
                    headers=_spotify_headers(token),
                )
                if feat_resp.status_code == 200:
                    for f in feat_resp.json().get("audio_features") or []:
                        if f:
                            features_map[f["id"]] = f

    # ── Create songs ──
    songs_created = 0
    for sp_track in sp_tracks:
        if not sp_track or not sp_track.get("id"):
            continue
        existing_song = db.query(models.Song).filter(models.Song.spotify_id == sp_track["id"]).first()
        if existing_song:
            continue
        f = features_map.get(sp_track["id"], {})
        duration_ms = sp_track.get("duration_ms")
        song = models.Song(
            title=sp_track["name"],
            artist_id=artist.id,
            album_id=album.id,
            duration_seconds=int(duration_ms / 1000) if duration_ms else None,
            track_number=sp_track.get("track_number"),
            spotify_id=sp_track["id"],
            spotify_preview_url=sp_track.get("preview_url"),
            danceability=f.get("danceability"),
            energy=f.get("energy"),
            valence=f.get("valence"),
            loudness=f.get("loudness"),
            tempo=f.get("tempo"),
            acousticness=f.get("acousticness"),
            instrumentalness=f.get("instrumentalness"),
        )
        db.add(song)
        songs_created += 1

    db.commit()
    db.refresh(album)

    # Fire-and-forget: embed the album, artist, and all its songs in the background
    from ..embeddings import reembed_album_bg, reembed_artist_bg, reembed_song_bg
    asyncio.create_task(reembed_artist_bg(artist.id))
    asyncio.create_task(reembed_album_bg(album.id))
    song_ids = [s.id for s in db.query(models.Song.id).filter(models.Song.album_id == album.id).all()]
    for sid in song_ids:
        asyncio.create_task(reembed_song_bg(sid))

    return {
        "album_id":        album.id,
        "song_count":      songs_created,
        "already_existed": False,
    }


# ── Artist import ─────────────────────────────────────────────────────────────

@router.post("/import-artist")
async def import_artist(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Import a Spotify artist into Tunelog and their top releases (up to 5 albums, singles, and EPs).
    Body: { spotify_artist_id: str }
    Returns { artist_id, albums_imported }
    """
    spotify_artist_id = body.get("spotify_artist_id")
    if not spotify_artist_id:
        raise HTTPException(status_code=400, detail="spotify_artist_id is required")

    token = await _get_client_token()

    async with httpx.AsyncClient(timeout=10.0) as client:
        art_resp = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_artist_id}",
            headers=_spotify_headers(token),
        )
        if art_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch artist from Spotify")
        sp_artist = art_resp.json()

        # Fetch albums + singles/EPs, latest first
        alb_resp = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_artist_id}/albums",
            params={"include_groups": "album,single", "limit": 5, "market": "US"},
            headers=_spotify_headers(token),
        )
        if alb_resp.status_code == 429:
            await asyncio.sleep(int(alb_resp.headers.get("Retry-After", 2)))
            alb_resp = await client.get(
                f"https://api.spotify.com/v1/artists/{spotify_artist_id}/albums",
                params={"include_groups": "album,single", "limit": 5, "market": "US"},
                headers=_spotify_headers(token),
            )
        sp_albums = alb_resp.json().get("items", []) if alb_resp.status_code == 200 else []

    # ── Resolve / create artist ──
    artist = db.query(models.Artist).filter(models.Artist.spotify_id == spotify_artist_id).first()
    if not artist:
        artist = db.query(models.Artist).filter(models.Artist.name.ilike(sp_artist["name"])).first()

    images = sp_artist.get("images") or []
    if artist:
        # Update image/spotify_id if missing
        if not artist.spotify_id:
            artist.spotify_id = spotify_artist_id
        if not artist.image_url and images:
            artist.image_url = images[0]["url"]
        db.flush()
    else:
        artist = models.Artist(
            name=sp_artist["name"],
            spotify_id=spotify_artist_id,
            image_url=images[0]["url"] if images else None,
        )
        db.add(artist)
        db.flush()

    # ── Save genres from Spotify ──
    _sync_artist_genres(artist, sp_artist.get("genres", []), db)

    # ── Import each album ──
    albums_imported = 0
    for sp_alb in sp_albums:
        if not sp_alb or not sp_alb.get("id"):
            continue
        existing = db.query(models.Album).filter(models.Album.spotify_id == sp_alb["id"]).first()
        if existing:
            continue

        # Fetch full album for tracks
        async with httpx.AsyncClient(timeout=10.0) as client:
            full_resp = await client.get(
                f"https://api.spotify.com/v1/albums/{sp_alb['id']}",
                headers=_spotify_headers(token),
            )
        if full_resp.status_code != 200:
            continue
        full_alb   = full_resp.json()
        alb_images = full_alb.get("images") or []
        rel_date   = full_alb.get("release_date", "")

        album = models.Album(
            title=full_alb["name"],
            artist_id=artist.id,
            spotify_id=full_alb["id"],
            cover_url=alb_images[0]["url"] if alb_images else None,
            release_date=rel_date[:4] if rel_date else None,
        )
        db.add(album)
        db.flush()
        _sync_album_genres(album, artist, db)

        # Tracks + audio features
        sp_tracks = full_alb.get("tracks", {}).get("items") or []
        track_ids = [t["id"] for t in sp_tracks if t and t.get("id")]
        features_map: dict = {}
        if track_ids:
            async with httpx.AsyncClient(timeout=10.0) as client:
                feat_resp = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    params={"ids": ",".join(track_ids[:100])},
                    headers=_spotify_headers(token),
                )
            if feat_resp.status_code == 200:
                for f in feat_resp.json().get("audio_features") or []:
                    if f:
                        features_map[f["id"]] = f

        for sp_track in sp_tracks:
            if not sp_track or not sp_track.get("id"):
                continue
            if db.query(models.Song).filter(models.Song.spotify_id == sp_track["id"]).first():
                continue
            f = features_map.get(sp_track["id"], {})
            duration_ms = sp_track.get("duration_ms")
            db.add(models.Song(
                title=sp_track["name"],
                artist_id=artist.id,
                album_id=album.id,
                duration_seconds=int(duration_ms / 1000) if duration_ms else None,
                track_number=sp_track.get("track_number"),
                spotify_id=sp_track["id"],
                spotify_preview_url=sp_track.get("preview_url"),
                danceability=f.get("danceability"),
                energy=f.get("energy"),
                valence=f.get("valence"),
                loudness=f.get("loudness"),
                tempo=f.get("tempo"),
                acousticness=f.get("acousticness"),
                instrumentalness=f.get("instrumentalness"),
            ))
            albums_imported += 1

    db.commit()

    # Fire-and-forget: embed the artist and all imported content in the background
    from ..embeddings import reembed_artist_bg, reembed_album_bg, reembed_song_bg
    asyncio.create_task(reembed_artist_bg(artist.id))
    album_ids = [a.id for a in db.query(models.Album.id).filter(models.Album.artist_id == artist.id).all()]
    for aid in album_ids:
        asyncio.create_task(reembed_album_bg(aid))
    song_ids = [s.id for s in db.query(models.Song.id).filter(models.Song.artist_id == artist.id).all()]
    for sid in song_ids:
        asyncio.create_task(reembed_song_bg(sid))

    return {"artist_id": artist.id, "albums_imported": albums_imported}
