import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

AVATARS_DIR = Path(__file__).parent.parent / "static" / "avatars"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/api/users", tags=["users"])


def _user_out(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "follower_count": len(user.followers),
        "following_count": len(user.following),
    }


@router.get("/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user)


@router.put("/me/profile", response_model=schemas.User)
def update_profile(
    update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if update.username is not None:
        new_username = update.username.strip()
        if not new_username:
            raise HTTPException(status_code=400, detail="Username cannot be empty")
        if new_username != current_user.username:
            taken = db.query(models.User).filter(
                models.User.username == new_username,
                models.User.id != current_user.id,
            ).first()
            if taken:
                raise HTTPException(status_code=409, detail="Username already taken")
            current_user.username = new_username
    if update.bio is not None:
        current_user.bio = update.bio
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url
    db.commit()
    db.refresh(current_user)
    current_user.follower_count = len(current_user.followers)
    current_user.following_count = len(current_user.following)
    return current_user


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are allowed")

    data = await file.read()
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    # Delete old avatar file if it was an uploaded one
    if current_user.avatar_url and current_user.avatar_url.startswith("/static/avatars/"):
        old_path = Path(__file__).parent.parent / current_user.avatar_url.lstrip("/")
        if old_path.exists():
            old_path.unlink()

    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    dest = AVATARS_DIR / filename
    dest.write_bytes(data)

    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()
    return {"avatar_url": current_user.avatar_url}


@router.post("/{username}/follow")
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    target = db.query(models.User).filter(models.User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    exists = db.query(models.UserFollow).filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Already following")

    db.add(models.UserFollow(follower_id=current_user.id, followed_id=target.id))
    db.add(models.Activity(
        user_id=current_user.id, action_type="followed",
        target_type="user", target_id=target.id,
    ))
    db.commit()
    return {"message": f"Now following {username}"}


@router.delete("/{username}/follow")
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    target = db.query(models.User).filter(models.User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    follow = db.query(models.UserFollow).filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if not follow:
        raise HTTPException(status_code=400, detail="Not following this user")

    db.delete(follow)
    db.commit()
    return {"message": f"Unfollowed {username}"}


@router.get("/{username}/follow-status")
def follow_status(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    target = db.query(models.User).filter(models.User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    following = db.query(models.UserFollow).filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first() is not None
    return {"following": following}


@router.get("/{username}/followers")
def get_followers(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [_user_out(f.follower) for f in user.followers]


@router.get("/{username}/following")
def get_following(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return [_user_out(f.followed) for f in user.following]


@router.get("/{username}/activity")
def get_user_activity(
    username: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rows = (
        db.query(models.Activity)
        .filter(models.Activity.user_id == user.id)
        .order_by(models.Activity.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return _enrich_activities(rows, db)


@router.get("/{username}/reviews")
def get_user_reviews(
    username: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reviews = (
        db.query(models.Review)
        .filter(models.Review.user_id == user.id)
        .order_by(models.Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    result = []
    for r in reviews:
        row = {
            "id": r.id, "rating": r.rating, "text": r.text,
            "created_at": r.created_at,
            "song_id": r.song_id, "album_id": r.album_id,
        }
        if r.album:
            row["target_title"] = r.album.title
            row["target_cover"] = r.album.cover_url
            row["target_type"] = "album"
            row["target_artist"] = r.album.artist.name
        elif r.song:
            row["target_title"] = r.song.title
            row["target_cover"] = r.song.album.cover_url if r.song.album else None
            row["target_type"] = "song"
            row["target_artist"] = r.song.artist.name
        result.append(row)
    return result


def _enrich_activities(activities, db) -> list:
    result = []
    for a in activities:
        d = {
            "id": a.id, "user_id": a.user_id,
            "username": a.user.username, "avatar_url": a.user.avatar_url,
            "action_type": a.action_type, "target_type": a.target_type,
            "target_id": a.target_id, "meta": a.meta,
            "created_at": a.created_at,
        }
        if a.target_type == "album" and a.target_id:
            album = db.query(models.Album).get(a.target_id)
            if album:
                d["target_name"]   = album.title
                d["target_cover"]  = album.cover_url
                d["target_artist"] = album.artist.name
                d["target_url"]    = f"/albums/{album.id}"
        elif a.target_type == "song" and a.target_id:
            song = db.query(models.Song).get(a.target_id)
            if song:
                d["target_name"]   = song.title
                d["target_artist"] = song.artist.name
                d["target_cover"]  = song.album.cover_url if song.album else None
                d["target_url"]    = f"/songs/{song.id}"
        elif a.target_type == "user" and a.target_id:
            u = db.query(models.User).get(a.target_id)
            if u:
                d["target_name"] = u.username
                d["target_url"]  = f"/users/{u.username}"
        result.append(d)
    return result
