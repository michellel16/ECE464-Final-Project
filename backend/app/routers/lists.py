from datetime import datetime, timedelta
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/lists", tags=["lists"])

COVERS_DIR = Path(__file__).parent.parent / "static" / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_COVER_BYTES = 5 * 1024 * 1024


def _delete_cover_file(cover_url: str | None) -> None:
    if cover_url and cover_url.startswith("/static/covers/"):
        path = COVERS_DIR / cover_url.split("/")[-1]
        path.unlink(missing_ok=True)


def _serialize_item(item: models.ListItem) -> dict:
    d = {
        "id": item.id, "list_id": item.list_id,
        "added_at": item.added_at, "notes": item.notes,
        "song_id": item.song_id, "album_id": item.album_id,
    }
    if item.song:
        d["type"]      = "song"
        d["title"]     = item.song.title
        d["artist"]    = item.song.artist.name
        d["cover_url"] = item.song.album.cover_url if item.song.album else None
        d["url"]       = f"/songs/{item.song.id}"
    elif item.album:
        d["type"]      = "album"
        d["title"]     = item.album.title
        d["artist"]    = item.album.artist.name
        d["cover_url"] = item.album.cover_url
        d["url"]       = f"/albums/{item.album.id}"
    return d


def _serialize_list(
    lst: models.List,
    include_items: bool = False,
    like_count: int = 0,
    is_liked: bool = False,
    include_owner: bool = False,
) -> dict:
    covers: list[str] = []
    for item in lst.items:
        if len(covers) >= 4:
            break
        cover = (item.album.cover_url if item.album else None) or \
                (item.song.album.cover_url if item.song and item.song.album else None)
        if cover and cover not in covers:
            covers.append(cover)

    d = {
        "id": lst.id, "user_id": lst.user_id, "name": lst.name,
        "description": lst.description, "list_type": lst.list_type,
        "is_public": lst.is_public, "created_at": lst.created_at,
        "item_count": len(lst.items),
        "like_count": like_count,
        "is_liked": is_liked,
        "cover_url":   lst.cover_url,
        "group_name":  lst.group_name,
        "cover_previews": covers,
    }
    if include_owner and lst.user:
        d["owner_username"]   = lst.user.username
        d["owner_avatar_url"] = lst.user.avatar_url
    if include_items:
        d["items"] = [_serialize_item(i) for i in lst.items]
    return d


def _batch_like_counts(db: Session, list_ids: list) -> dict:
    if not list_ids:
        return {}
    return dict(
        db.query(models.ListLike.list_id, func.count(models.ListLike.user_id))
        .filter(models.ListLike.list_id.in_(list_ids))
        .group_by(models.ListLike.list_id)
        .all()
    )


def _viewer_liked_set(db: Session, list_ids: list, viewer_id: Optional[int]) -> set:
    if not list_ids or not viewer_id:
        return set()
    return {
        row[0] for row in
        db.query(models.ListLike.list_id)
        .filter(models.ListLike.list_id.in_(list_ids), models.ListLike.user_id == viewer_id)
        .all()
    }


@router.get("/me")
def get_my_lists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lists = (
        db.query(models.List)
        .options(
            joinedload(models.List.items).joinedload(models.ListItem.album),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.album),
        )
        .filter(models.List.user_id == current_user.id)
        .all()
    )
    list_ids = [l.id for l in lists]
    like_counts = _batch_like_counts(db, list_ids)
    return [_serialize_list(l, like_count=like_counts.get(l.id, 0)) for l in lists]


@router.get("/saved")
def get_saved_lists(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lists that the current user has liked (from other users)."""
    liked_ids = [
        row[0] for row in
        db.query(models.ListLike.list_id)
        .filter(models.ListLike.user_id == current_user.id)
        .all()
    ]
    if not liked_ids:
        return []
    lists = (
        db.query(models.List)
        .options(
            joinedload(models.List.user),
            joinedload(models.List.items).joinedload(models.ListItem.album),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.album),
        )
        .filter(models.List.id.in_(liked_ids), models.List.is_public == True)
        .all()
    )
    like_counts = _batch_like_counts(db, [l.id for l in lists])
    return [
        _serialize_list(l, like_count=like_counts.get(l.id, 0), is_liked=True, include_owner=True)
        for l in lists
    ]


@router.get("/top")
def top_lists(
    limit: int = 20,
    skip: int = 0,
    sort: str = "top",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional),
):
    """Public lists ranked by like count (sort=top) or recent activity (sort=trending)."""
    lists = (
        db.query(models.List)
        .options(
            joinedload(models.List.user),
            joinedload(models.List.items).joinedload(models.ListItem.album),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.album),
        )
        .filter(models.List.is_public == True)
        .all()
    )

    list_ids     = [l.id for l in lists]
    like_counts  = _batch_like_counts(db, list_ids)
    viewer_liked = _viewer_liked_set(db, list_ids, current_user.id if current_user else None)

    if sort == "trending":
        cutoff = datetime.utcnow() - timedelta(days=30)
        trending_counts = dict(
            db.query(models.ListLike.list_id, func.count(models.ListLike.user_id))
            .filter(
                models.ListLike.list_id.in_(list_ids),
                models.ListLike.created_at >= cutoff,
            )
            .group_by(models.ListLike.list_id)
            .all()
        )
        sorted_lists = sorted(
            lists,
            key=lambda l: (-trending_counts.get(l.id, 0), -like_counts.get(l.id, 0), -len(l.items)),
        )
    else:
        sorted_lists = sorted(lists, key=lambda l: (-like_counts.get(l.id, 0), -len(l.items)))

    paginated    = sorted_lists[skip : skip + limit]

    result = []
    for l in paginated:
        covers: list[str] = []
        for item in l.items:
            if len(covers) >= 4:
                break
            cover = None
            if item.album and item.album.cover_url:
                cover = item.album.cover_url
            elif item.song and item.song.album and item.song.album.cover_url:
                cover = item.song.album.cover_url
            if cover and cover not in covers:
                covers.append(cover)

        result.append({
            "id": l.id,
            "name": l.name,
            "description": l.description,
            "list_type": l.list_type,
            "item_count": len(l.items),
            "like_count": like_counts.get(l.id, 0),
            "is_liked": l.id in viewer_liked,
            "owner_username": l.user.username if l.user else None,
            "owner_avatar_url": l.user.avatar_url if l.user else None,
            "cover_url": l.cover_url,
            "cover_previews": covers,
        })

    return result


@router.post("/{list_id}/like")
def toggle_like(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot like your own list")
    if not lst.is_public:
        raise HTTPException(status_code=403, detail="Cannot like a private list")

    existing = db.query(models.ListLike).filter_by(user_id=current_user.id, list_id=list_id).first()
    if existing:
        db.delete(existing)
    else:
        db.add(models.ListLike(user_id=current_user.id, list_id=list_id))
    db.commit()

    like_count = db.query(func.count(models.ListLike.user_id)).filter_by(list_id=list_id).scalar() or 0
    return {"liked": existing is None, "like_count": like_count}


@router.post("/{list_id}/fork", status_code=201)
def fork_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Copy a public list into the current user's account as an editable private copy."""
    src = (
        db.query(models.List)
        .options(joinedload(models.List.items))
        .filter(models.List.id == list_id)
        .first()
    )
    if not src:
        raise HTTPException(status_code=404, detail="List not found")
    if not src.is_public:
        raise HTTPException(status_code=403, detail="Cannot copy a private list")
    if src.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot copy your own list")

    new_list = models.List(
        user_id=current_user.id,
        name=f"{src.name} (copy)",
        description=src.description,
        list_type=src.list_type,
        is_public=False,
    )
    db.add(new_list)
    db.flush()

    for item in src.items:
        db.add(models.ListItem(
            list_id=new_list.id,
            song_id=item.song_id,
            album_id=item.album_id,
            notes=item.notes,
        ))

    db.commit()
    db.refresh(new_list)
    return _serialize_list(new_list)


@router.post("/", status_code=201)
def create_list(
    data: schemas.ListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = models.List(
        user_id=current_user.id, name=data.name,
        description=data.description, list_type=data.list_type,
        is_public=data.is_public,
    )
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return _serialize_list(lst)


@router.post("/covers", status_code=201)
async def upload_cover(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are allowed")
    data = await file.read()
    if len(data) > _MAX_COVER_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"
    (COVERS_DIR / filename).write_bytes(data)
    return {"url": f"/static/covers/{filename}"}


@router.get("/user/{username}")
def get_user_lists(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    lists = (
        db.query(models.List)
        .options(
            joinedload(models.List.items).joinedload(models.ListItem.album),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.album),
        )
        .filter(models.List.user_id == user.id, models.List.is_public == True)
        .all()
    )
    list_ids = [l.id for l in lists]
    like_counts  = _batch_like_counts(db, list_ids)
    viewer_liked = _viewer_liked_set(db, list_ids, current_user.id if current_user else None)
    return [
        _serialize_list(l, like_count=like_counts.get(l.id, 0), is_liked=l.id in viewer_liked)
        for l in lists
    ]


@router.get("/{list_id}")
def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional),
):
    lst = (
        db.query(models.List)
        .options(
            joinedload(models.List.user),
            joinedload(models.List.items).joinedload(models.ListItem.album).joinedload(models.Album.artist),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.album),
            joinedload(models.List.items).joinedload(models.ListItem.song).joinedload(models.Song.artist),
        )
        .filter(models.List.id == list_id)
        .first()
    )
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    like_count = db.query(func.count(models.ListLike.user_id)).filter_by(list_id=list_id).scalar() or 0
    is_liked = False
    if current_user and current_user.id != lst.user_id:
        is_liked = db.query(models.ListLike).filter_by(
            user_id=current_user.id, list_id=list_id
        ).first() is not None
    return _serialize_list(lst, include_items=True, like_count=like_count, is_liked=is_liked, include_owner=True)


@router.put("/{list_id}")
def update_list(
    list_id: int,
    data: schemas.ListCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    new_cover = data.cover_url or None
    if lst.cover_url != new_cover:
        _delete_cover_file(lst.cover_url)
    lst.name        = data.name
    lst.description = data.description
    lst.list_type   = data.list_type
    lst.is_public   = data.is_public
    lst.cover_url   = new_cover
    lst.group_name  = data.group_name or None
    db.commit()
    db.refresh(lst)
    return _serialize_list(lst)


@router.delete("/{list_id}")
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    _delete_cover_file(lst.cover_url)
    db.delete(lst)
    db.commit()
    return {"message": "List deleted"}


@router.post("/{list_id}/items", status_code=201)
def add_item(
    list_id: int,
    item: schemas.ListItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    new_item = models.ListItem(
        list_id=list_id, song_id=item.song_id,
        album_id=item.album_id, notes=item.notes,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return _serialize_item(new_item)


@router.delete("/{list_id}/items/{item_id}")
def remove_item(
    list_id: int, item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst or lst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    item = db.query(models.ListItem).filter(models.ListItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item removed"}
