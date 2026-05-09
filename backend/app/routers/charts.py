from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/charts", tags=["charts"])

PAGE_SIZE = 25

# ── Genre normalisation rules ─────────────────────────────────────────────────

# Merge: lower-cased source name → canonical target name
_GENRE_MERGE_RULES: dict[str, str] = {
    # K-Pop — cover both hyphenated and non-hyphenated, all generation variants
    "kpop": "K-Pop",
    "k-pop": "K-Pop",
    "k pop": "K-Pop",
    "korean pop": "K-Pop",
    "gen kpop": "K-Pop",
    "gen k-pop": "K-Pop",
    "1st gen kpop": "K-Pop",
    "1st gen k-pop": "K-Pop",
    "2nd gen kpop": "K-Pop",
    "2nd gen k-pop": "K-Pop",
    "3rd gen kpop": "K-Pop",
    "3rd gen k-pop": "K-Pop",
    "4th gen kpop": "K-Pop",
    "4th gen k-pop": "K-Pop",
    "5th gen kpop": "K-Pop",
    "5th gen k-pop": "K-Pop",
    # R&B
    "rnb": "R&B",
    "rhythm and blues": "R&B",
    "contemporary r b": "R&B",
    # Hip-Hop
    "hip hop": "Hip-Hop",
    "hip-hop": "Hip-Hop",
    "gangsta rap": "Hip-Hop",
    "trap": "Hip-Hop",
    "trap music": "Hip-Hop",
    # Electronic
    "electronica": "Electronic",
    "electronic music": "Electronic",
    "edm": "Electronic",
    "electropop": "Electronic",
    # Rock
    "classic rock": "Rock",
    "alt rock": "Alternative Rock",
    # Pop
    "pop music": "Pop",
    "dance pop": "Pop",
    "dance-pop": "Pop",
    # Synth-Pop duplicates
    "synthpop": "Synth-Pop",
    # Darkwave duplicates
    "dark wave": "Darkwave",
}

# Split: lower-cased source name → list of canonical targets (source is deleted)
_GENRE_SPLIT_RULES: dict[str, list[str]] = {
    "r&b/soul": ["R&B", "Soul"],
    "hip-hop/rap": ["Hip-Hop"],
    "pop/rock": ["Pop", "Rock"],
    "folk/country": ["Folk", "Country"],
    "jazz & blues": ["Jazz", "Blues"],
}


def _do_fix_genres(db: Session) -> dict:
    """
    Apply merge + split rules to normalise genre names.
    Re-links artist_genre / album_genre rows and removes stale Genre rows.
    """
    all_genres = db.query(models.Genre).all()
    genre_by_name: dict[str, models.Genre] = {g.name: g for g in all_genres}
    genre_by_id:   dict[int, models.Genre] = {g.id:   g for g in all_genres}

    def _get_or_create(name: str) -> models.Genre:
        if name not in genre_by_name:
            g = models.Genre(name=name)
            db.add(g)
            db.flush()
            genre_by_name[name] = g
            genre_by_id[g.id]   = g
        return genre_by_name[name]

    to_delete: set[int] = set()

    def _reassign(old_id: int, new_ids: list[int]):
        """Move every artist_genre / album_genre row from old_id to new_ids."""
        for new_id in new_ids:
            # artist_genre
            db.execute(text("""
                INSERT INTO artist_genre (artist_id, genre_id)
                SELECT artist_id, :new_id FROM artist_genre
                WHERE genre_id = :old_id
                ON CONFLICT DO NOTHING
            """), {"old_id": old_id, "new_id": new_id})
            # album_genre
            db.execute(text("""
                INSERT INTO album_genre (album_id, genre_id)
                SELECT album_id, :new_id FROM album_genre
                WHERE genre_id = :old_id
                ON CONFLICT DO NOTHING
            """), {"old_id": old_id, "new_id": new_id})
        # Remove old associations
        db.execute(text("DELETE FROM artist_genre WHERE genre_id = :id"), {"id": old_id})
        db.execute(text("DELETE FROM album_genre  WHERE genre_id = :id"), {"id": old_id})
        to_delete.add(old_id)

    merges_done = 0
    splits_done = 0

    for genre in list(all_genres):
        lname = genre.name.lower()

        # Check split rules first
        if lname in _GENRE_SPLIT_RULES:
            targets = [_get_or_create(n) for n in _GENRE_SPLIT_RULES[lname]]
            target_ids = [t.id for t in targets]
            if genre.id not in target_ids:   # avoid self-loop
                _reassign(genre.id, target_ids)
                splits_done += 1
            continue

        # Check merge rules
        if lname in _GENRE_MERGE_RULES:
            canonical = _GENRE_MERGE_RULES[lname]
            target = _get_or_create(canonical)
            if genre.id != target.id:
                _reassign(genre.id, [target.id])
                merges_done += 1

    # Delete orphaned genre rows
    if to_delete:
        db.execute(
            text(f"DELETE FROM genres WHERE id IN ({','.join(str(i) for i in to_delete)})")
        )
    db.commit()
    return {"merges": merges_done, "splits": splits_done, "removed": len(to_delete)}

# Known genre mappings for seed data — used to repair missing associations
_SEED_ARTIST_GENRES: dict[str, list[str]] = {
    "Taylor Swift":   ["Pop", "Folk", "Indie"],
    "The Beatles":    ["Rock", "Pop"],
    "Kendrick Lamar": ["Hip-Hop"],
    "Radiohead":      ["Alternative", "Rock", "Electronic"],
    "Frank Ocean":    ["R&B", "Indie", "Hip-Hop"],
}

_SEED_ALBUM_GENRES: dict[str, list[str]] = {
    "Folklore":                              ["Folk", "Indie", "Pop"],
    "1989":                                  ["Pop"],
    "Midnights":                             ["Pop", "Electronic"],
    "Abbey Road":                            ["Rock", "Pop"],
    "Sgt. Pepper's Lonely Hearts Club Band": ["Rock", "Pop"],
    "To Pimp a Butterfly":                   ["Hip-Hop"],
    "DAMN.":                                 ["Hip-Hop"],
    "OK Computer":                           ["Alternative", "Rock"],
    "Kid A":                                 ["Alternative", "Electronic"],
    "Blonde":                                ["R&B", "Indie"],
    "channel ORANGE":                        ["R&B", "Hip-Hop"],
}


def _do_propagate_genres(db: Session) -> dict:
    """
    Idempotent: assigns known genres to seed artists/albums that have none,
    then copies artist genres to any album still without genres.
    """
    genre_map = {g.name: g for g in db.query(models.Genre).all()}

    def _get_genre(name: str) -> models.Genre:
        if name not in genre_map:
            g = models.Genre(name=name)
            db.add(g)
            db.flush()
            genre_map[name] = g
        return genre_map[name]

    artists_tagged = 0
    for artist in db.query(models.Artist).options(joinedload(models.Artist.genres)).all():
        if not artist.genres and artist.name in _SEED_ARTIST_GENRES:
            existing_ids = {g.id for g in artist.genres}
            for gname in _SEED_ARTIST_GENRES[artist.name]:
                g = _get_genre(gname)
                if g.id not in existing_ids:
                    artist.genres.append(g)
                    existing_ids.add(g.id)
            artists_tagged += 1
    db.flush()

    albums_tagged = 0
    for album in (
        db.query(models.Album)
        .options(
            joinedload(models.Album.genres),
            joinedload(models.Album.artist).joinedload(models.Artist.genres),
        )
        .all()
    ):
        if album.genres:
            continue
        existing_ids: set[int] = set()
        if album.title in _SEED_ALBUM_GENRES:
            for gname in _SEED_ALBUM_GENRES[album.title]:
                g = _get_genre(gname)
                if g.id not in existing_ids:
                    album.genres.append(g)
                    existing_ids.add(g.id)
            albums_tagged += 1
        elif album.artist and album.artist.genres:
            for g in album.artist.genres:
                album.genres.append(g)
            albums_tagged += 1

    db.commit()
    return {"artists_tagged": artists_tagged, "albums_tagged": albums_tagged}


def _used_genre_ids(db: Session) -> set[int]:
    """Return IDs of genres linked to at least one artist or album."""
    from_artists = {r[0] for r in db.query(models.artist_genre.c.genre_id).distinct().all()}
    from_albums  = {r[0] for r in db.query(models.album_genre.c.genre_id).distinct().all()}
    return from_artists | from_albums


def _do_cleanup_genres(db: Session) -> int:
    """Delete Genre rows that have no artist or album associations."""
    used_ids = _used_genre_ids(db)
    if not used_ids:
        # Nothing is linked yet — don't nuke the Genre table
        return 0
    deleted = (
        db.query(models.Genre)
        .filter(models.Genre.id.notin_(used_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


@router.post("/propagate-genres")
def propagate_genres(db: Session = Depends(get_db)):
    """Assign known genres to untagged artists/albums, then remove unused genre rows."""
    result = _do_propagate_genres(db)
    result["genres_removed"] = _do_cleanup_genres(db)
    return result


@router.get("/albums")
def top_albums(
    year: Optional[int] = None,
    decade: Optional[int] = None,
    genre_id: Optional[int] = None,
    limit: int = 25,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    has_filter = bool(year or decade or genre_id)

    if has_filter:
        # When filtering: LEFT JOIN so albums without reviews still appear,
        # coalesce NULL avg to 0 so they sort to the bottom.
        q = (
            db.query(
                models.Album.id,
                func.coalesce(func.avg(models.Review.rating), 0).label("avg_rating"),
                func.count(models.Review.id).label("review_count"),
            )
            .outerjoin(models.Review, models.Review.album_id == models.Album.id)
            .group_by(models.Album.id)
        )
    else:
        # Default chart: only albums that have been reviewed
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

    total = q.count()

    rows = (
        q.order_by(
            func.coalesce(func.avg(models.Review.rating), 0).desc(),
            func.count(models.Review.id).desc(),
        )
        .offset(skip).limit(limit)
        .all()
    )

    if not rows:
        return {"items": [], "total": total}

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

    return {
        "total": total,
        "items": [
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
        ],
    }


@router.get("/genres")
def chart_genres(db: Session = Depends(get_db)):
    used_ids = _used_genre_ids(db)
    if not used_ids:
        return []
    genres = (
        db.query(models.Genre)
        .filter(models.Genre.id.in_(used_ids))
        .order_by(models.Genre.name)
        .all()
    )
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


@router.get("/all-genres-debug")
def all_genres_debug(db: Session = Depends(get_db)):
    """Return every genre name in the DB — for debugging normalisation rules."""
    return sorted([g.name for g in db.query(models.Genre).all()])


@router.post("/fix-genres")
def fix_genres(db: Session = Depends(get_db)):
    """Normalise genre names (merge variants, split compound genres)."""
    return _do_fix_genres(db)


@router.get("/artists")
def top_artists(
    genre_id: Optional[int] = None,
    limit: int = 25,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            models.Artist.id,
            func.avg(models.Review.rating).label("avg_rating"),
            func.count(models.Review.id).label("review_count"),
        )
        .join(models.Album, models.Album.artist_id == models.Artist.id)
        .join(models.Review, models.Review.album_id == models.Album.id)
        .group_by(models.Artist.id)
        .having(func.count(models.Review.id) >= 1)
    )

    if genre_id:
        genre_sub = (
            db.query(models.artist_genre.c.artist_id)
            .filter(models.artist_genre.c.genre_id == genre_id)
            .subquery()
        )
        q = q.filter(models.Artist.id.in_(genre_sub))

    total = q.count()

    rows = (
        q.order_by(func.avg(models.Review.rating).desc(), func.count(models.Review.id).desc())
        .offset(skip).limit(limit)
        .all()
    )

    if not rows:
        return {"items": [], "total": total}

    artist_ids = [r.id for r in rows]
    stats = {r.id: (round(float(r.avg_rating), 2), r.review_count) for r in rows}

    artists = {
        a.id: a for a in (
            db.query(models.Artist)
            .options(joinedload(models.Artist.genres))
            .filter(models.Artist.id.in_(artist_ids))
            .all()
        )
    }

    return {
        "total": total,
        "items": [
            {
                "rank": skip + i + 1,
                "artist": {
                    "id": artists[aid].id,
                    "name": artists[aid].name,
                    "image_url": getattr(artists[aid], "image_url", None),
                    "genres": [{"id": g.id, "name": g.name} for g in artists[aid].genres],
                },
                "average_rating": stats[aid][0],
                "review_count": stats[aid][1],
            }
            for i, aid in enumerate(artist_ids)
            if aid in artists
        ],
    }


@router.get("/songs")
def top_songs(
    genre_id: Optional[int] = None,
    limit: int = 25,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            models.Song.id,
            func.avg(models.Review.rating).label("avg_rating"),
            func.count(models.Review.id).label("review_count"),
        )
        .join(models.Review, models.Review.song_id == models.Song.id)
        .group_by(models.Song.id)
        .having(func.count(models.Review.id) >= 1)
    )

    if genre_id:
        genre_sub = (
            db.query(models.artist_genre.c.artist_id)
            .filter(models.artist_genre.c.genre_id == genre_id)
            .subquery()
        )
        q = q.filter(models.Song.artist_id.in_(genre_sub))

    total = q.count()

    rows = (
        q.order_by(func.avg(models.Review.rating).desc(), func.count(models.Review.id).desc())
        .offset(skip).limit(limit)
        .all()
    )

    if not rows:
        return {"items": [], "total": total}

    song_ids = [r.id for r in rows]
    stats = {r.id: (round(float(r.avg_rating), 2), r.review_count) for r in rows}

    songs = {
        s.id: s for s in (
            db.query(models.Song)
            .options(joinedload(models.Song.artist), joinedload(models.Song.album))
            .filter(models.Song.id.in_(song_ids))
            .all()
        )
    }

    return {
        "total": total,
        "items": [
            {
                "rank": skip + i + 1,
                "song": {
                    "id": songs[sid].id,
                    "title": songs[sid].title,
                    "artist": {"id": songs[sid].artist.id, "name": songs[sid].artist.name},
                    "album": (
                        {
                            "id": songs[sid].album.id,
                            "title": songs[sid].album.title,
                            "cover_url": songs[sid].album.cover_url,
                        }
                        if songs[sid].album else None
                    ),
                },
                "average_rating": stats[sid][0],
                "review_count": stats[sid][1],
            }
            for i, sid in enumerate(song_ids)
            if sid in songs
        ],
    }
