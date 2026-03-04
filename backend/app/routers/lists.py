from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/lists", tags=["lists"])


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


def _serialize_list(lst: models.List, include_items: bool = False) -> dict:
    d = {
        "id": lst.id, "user_id": lst.user_id, "name": lst.name,
        "description": lst.description, "list_type": lst.list_type,
        "is_public": lst.is_public, "created_at": lst.created_at,
        "item_count": len(lst.items),
    }
    if include_items:
        d["items"] = [_serialize_item(i) for i in lst.items]
    return d


@router.get("/me")
def get_my_lists(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lists = db.query(models.List).filter(models.List.user_id == current_user.id).all()
    return [_serialize_list(l) for l in lists]


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


@router.get("/user/{username}")
def get_user_lists(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    lists = db.query(models.List).filter(
        models.List.user_id == user.id, models.List.is_public == True
    ).all()
    return [_serialize_list(l) for l in lists]


@router.get("/{list_id}")
def get_list(list_id: int, db: Session = Depends(get_db)):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    return _serialize_list(lst, include_items=True)


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
    lst.name = data.name
    lst.description = data.description
    lst.list_type = data.list_type
    lst.is_public = data.is_public
    db.commit()
    db.refresh(lst)
    return _serialize_list(lst)


@router.delete("/{list_id}")
def delete_list(list_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    lst = db.query(models.List).filter(models.List.id == list_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if lst.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
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
