import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_user_optional

AVATARS_DIR  = Path(__file__).parent.parent / "static" / "avatars"
BANNERS_DIR  = Path(__file__).parent.parent / "static" / "banners"
BANNERS_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/api/users", tags=["users"])


def _can_view(viewer: Optional[models.User], profile_user: models.User, db) -> bool:
    """Return True if viewer is allowed to see a private user's content."""
    if not profile_user.is_private:
        return True
    if viewer is None:
        return False
    if viewer.id == profile_user.id:
        return True
    return db.query(models.UserFollow).filter_by(
        follower_id=viewer.id, followed_id=profile_user.id
    ).first() is not None


def _user_out(user: models.User, db=None) -> dict:
    try:
        prefs = json.loads(user.music_preferences or '{}')
    except Exception:
        prefs = {}
    if db is not None:
        follower_count  = db.query(func.count(models.UserFollow.follower_id)).filter_by(followed_id=user.id).scalar() or 0
        following_count = db.query(func.count(models.UserFollow.followed_id)).filter_by(follower_id=user.id).scalar() or 0
    else:
        follower_count  = len(user.followers)
        following_count = len(user.following)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "follower_count": follower_count,
        "following_count": following_count,
        "is_private": user.is_private or False,
        "music_preferences": prefs,
        "banner_url": user.banner_url,
    }


@router.get("/suggested")
def suggested_users(
    limit: int = 6,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Second-degree connections: users followed by people I follow.
    Falls back to most-followed users when the current user follows no one."""
    my_following_ids = {f.followed_id for f in current_user.following}
    my_following_ids.add(current_user.id)  # always exclude self

    if len(my_following_ids) == 1:
        # No follows yet — return most-followed users via SQL COUNT (no lazy loads)
        follower_count_sub = (
            db.query(models.UserFollow.followed_id, func.count(models.UserFollow.follower_id).label("cnt"))
            .group_by(models.UserFollow.followed_id)
            .subquery()
        )
        users = (
            db.query(models.User)
            .outerjoin(follower_count_sub, follower_count_sub.c.followed_id == models.User.id)
            .filter(models.User.id != current_user.id)
            .order_by(func.coalesce(follower_count_sub.c.cnt, 0).desc())
            .limit(limit)
            .all()
        )
        return [_user_out(u, db) for u in users]

    # Tally mutual follow candidates in one SQL query
    followed_ids_list = list(my_following_ids - {current_user.id})
    rows = (
        db.query(models.UserFollow.followed_id, func.count(models.UserFollow.follower_id).label("cnt"))
        .filter(
            models.UserFollow.follower_id.in_(followed_ids_list),
            models.UserFollow.followed_id.notin_(my_following_ids),
        )
        .group_by(models.UserFollow.followed_id)
        .order_by(func.count(models.UserFollow.follower_id).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []

    candidate_ids = [r[0] for r in rows]
    candidate_score = {r[0]: r[1] for r in rows}
    users_map = {
        u.id: u for u in db.query(models.User).filter(models.User.id.in_(candidate_ids)).all()
    }
    result = []
    for uid in candidate_ids:
        u = users_map.get(uid)
        if u:
            out = _user_out(u, db)
            out["mutual_follows"] = candidate_score[uid]
            result.append(out)
    return result


@router.get("/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user, db)


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
        if new_username.lower() != current_user.username.lower():
            taken = db.query(models.User).filter(
                func.lower(models.User.username) == new_username.lower(),
                models.User.id != current_user.id,
            ).first()
            if taken:
                raise HTTPException(status_code=409, detail="Username already taken")
            current_user.username = new_username
    if update.bio is not None:
        current_user.bio = update.bio
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url
    if update.banner_url is not None:
        current_user.banner_url = update.banner_url
    if update.is_private is not None:
        current_user.is_private = update.is_private
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


@router.post("/me/banner")
async def upload_banner(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are allowed")
    data = await file.read()
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    if current_user.banner_url and current_user.banner_url.startswith("/static/banners/"):
        old_path = Path(__file__).parent.parent / current_user.banner_url.lstrip("/")
        if old_path.exists():
            old_path.unlink()

    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    dest = BANNERS_DIR / filename
    dest.write_bytes(data)

    current_user.banner_url = f"/static/banners/{filename}"
    db.commit()
    return {"banner_url": current_user.banner_url}


@router.delete("/me/banner")
def remove_banner(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.banner_url and current_user.banner_url.startswith("/static/banners/"):
        old_path = Path(__file__).parent.parent / current_user.banner_url.lstrip("/")
        if old_path.exists():
            old_path.unlink()
    current_user.banner_url = None
    db.commit()
    return {"banner_url": None}


@router.get("/me/preferences")
def get_preferences(current_user: models.User = Depends(get_current_user)):
    try:
        prefs = json.loads(current_user.music_preferences or '{}')
    except Exception:
        prefs = {}
    return prefs


@router.put("/me/preferences")
def update_preferences(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    genres    = [str(g)[:60] for g in (body.get('genres') or []) if g][:12]
    moods     = [str(m)[:40] for m in (body.get('moods')  or []) if m][:12]
    free_text = str(body.get('free_text') or '').strip()[:300]

    prefs = {'genres': genres, 'moods': moods, 'free_text': free_text}
    current_user.music_preferences = json.dumps(prefs)
    current_user.taste_profile_hash = None  # force taste embedding refresh
    db.commit()
    return prefs


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

    already = db.query(models.UserFollow).filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Already following")

    if target.is_private:
        # Check for existing pending request
        existing_req = db.query(models.FollowRequest).filter_by(
            requester_id=current_user.id, target_id=target.id
        ).first()
        if existing_req:
            raise HTTPException(status_code=400, detail="Follow request already sent")
        db.add(models.FollowRequest(requester_id=current_user.id, target_id=target.id))
        db.add(models.Notification(
            user_id=target.id, type="follow_request", from_user_id=current_user.id,
        ))
        db.commit()
        return {"message": "Follow request sent", "requested": True}

    db.add(models.UserFollow(follower_id=current_user.id, followed_id=target.id))
    db.add(models.Activity(
        user_id=current_user.id, action_type="followed",
        target_type="user", target_id=target.id,
    ))
    db.add(models.Notification(
        user_id=target.id, type="new_follower", from_user_id=current_user.id,
    ))
    db.commit()
    return {"message": f"Now following {username}", "requested": False}


@router.delete("/{username}/follow")
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    target = db.query(models.User).filter(models.User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Cancel a pending request if one exists
    pending = db.query(models.FollowRequest).filter_by(
        requester_id=current_user.id, target_id=target.id
    ).first()
    if pending:
        db.delete(pending)
        db.commit()
        return {"message": "Follow request cancelled"}

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
    requested = (not following) and db.query(models.FollowRequest).filter_by(
        requester_id=current_user.id, target_id=target.id
    ).first() is not None
    return {"following": following, "requested": requested}


@router.get("/me/following")
def get_following(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Users the current user follows."""
    following_ids = [f.followed_id for f in current_user.following]
    if not following_ids:
        return []
    users = db.query(models.User).filter(models.User.id.in_(following_ids)).all()
    return [{"username": u.username, "avatar_url": u.avatar_url} for u in users]


@router.get("/me/mutual-follows")
def get_mutual_follows(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Users who both follow me and I follow (mutual)."""
    following_ids = {f.followed_id for f in current_user.following}
    follower_ids  = {f.follower_id  for f in current_user.followers}
    mutual_ids    = following_ids & follower_ids
    if not mutual_ids:
        return []
    users = db.query(models.User).filter(models.User.id.in_(mutual_ids)).all()
    return [{"username": u.username, "avatar_url": u.avatar_url} for u in users]


@router.get("/me/follow-requests")
def get_follow_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    requests = (
        db.query(models.FollowRequest)
        .filter_by(target_id=current_user.id)
        .order_by(models.FollowRequest.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "requester_username": r.requester.username,
            "requester_avatar_url": r.requester.avatar_url,
            "created_at": r.created_at,
        }
        for r in requests
    ]


@router.post("/me/follow-requests/{request_id}/accept")
def accept_follow_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.FollowRequest).filter_by(
        id=request_id, target_id=current_user.id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    db.add(models.UserFollow(follower_id=req.requester_id, followed_id=current_user.id))
    db.add(models.Activity(
        user_id=req.requester_id, action_type="followed",
        target_type="user", target_id=current_user.id,
    ))
    db.add(models.Notification(
        user_id=req.requester_id, type="new_follower", from_user_id=current_user.id,
    ))
    db.delete(req)
    db.commit()
    return {"message": "Request accepted"}


@router.post("/me/follow-requests/{request_id}/reject")
def reject_follow_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.FollowRequest).filter_by(
        id=request_id, target_id=current_user.id
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(req)
    db.commit()
    return {"message": "Request rejected"}


@router.get("/{username}/followers")
def get_followers(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_view(current_user, user, db):
        raise HTTPException(status_code=403, detail="This account is private")
    return [_user_out(f.follower, db) for f in user.followers]


@router.get("/{username}/following")
def get_following(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_view(current_user, user, db):
        raise HTTPException(status_code=403, detail="This account is private")
    return [_user_out(f.followed, db) for f in user.following]


@router.get("/{username}/activity")
def get_user_activity(
    username: str,
    skip: int = 0,
    limit: int = 20,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_view(current_user, user, db):
        raise HTTPException(status_code=403, detail="This account is private")
    q = (
        db.query(models.Activity)
        .options(joinedload(models.Activity.user))
        .filter(models.Activity.user_id == user.id)
    )
    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.filter(models.Activity.created_at >= cutoff)
    rows = q.order_by(models.Activity.created_at.desc()).offset(skip).limit(limit).all()
    return _enrich_activities(rows, db)


@router.get("/{username}/reviews")
def get_user_reviews(
    username: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_view(current_user, user, db):
        raise HTTPException(status_code=403, detail="This account is private")
    reviews = (
        db.query(models.Review)
        .options(
            joinedload(models.Review.album).joinedload(models.Album.artist),
            joinedload(models.Review.song).joinedload(models.Song.artist),
            joinedload(models.Review.song).joinedload(models.Song.album),
        )
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
            row["target_artist"] = r.album.artist.name if r.album.artist else None
        elif r.song:
            row["target_title"] = r.song.title
            row["target_cover"] = r.song.album.cover_url if r.song.album else None
            row["target_album_title"] = r.song.album.title if r.song.album else None
            row["target_type"] = "song"
            row["target_artist"] = r.song.artist.name if r.song.artist else None
        result.append(row)
    return result


def _enrich_activities(activities, db) -> list:
    if not activities:
        return []

    # Batch-fetch all referenced targets in 3 queries instead of N
    album_ids = {a.target_id for a in activities if a.target_type == "album" and a.target_id}
    song_ids  = {a.target_id for a in activities if a.target_type == "song"  and a.target_id}
    user_ids  = {a.target_id for a in activities if a.target_type == "user"  and a.target_id}

    albums = {}
    if album_ids:
        for al in (
            db.query(models.Album)
            .options(joinedload(models.Album.artist))
            .filter(models.Album.id.in_(album_ids))
            .all()
        ):
            albums[al.id] = al

    songs = {}
    if song_ids:
        for s in (
            db.query(models.Song)
            .options(joinedload(models.Song.artist), joinedload(models.Song.album))
            .filter(models.Song.id.in_(song_ids))
            .all()
        ):
            songs[s.id] = s

    users = {}
    if user_ids:
        for u in db.query(models.User).filter(models.User.id.in_(user_ids)).all():
            users[u.id] = u

    result = []
    for a in activities:
        # Skip activities whose target has since been deleted
        if a.target_type == "album" and a.target_id and a.target_id not in albums:
            continue
        if a.target_type == "song" and a.target_id and a.target_id not in songs:
            continue

        d = {
            "id": a.id, "user_id": a.user_id,
            "username": a.user.username, "avatar_url": a.user.avatar_url,
            "action_type": a.action_type, "target_type": a.target_type,
            "target_id": a.target_id, "meta": a.meta,
            "created_at": a.created_at,
        }
        if a.target_type == "album" and a.target_id:
            album = albums.get(a.target_id)
            if album:
                d["target_name"]   = album.title
                d["target_cover"]  = album.cover_url
                d["target_artist"] = album.artist.name
                d["target_url"]    = f"/albums/{album.id}"
        elif a.target_type == "song" and a.target_id:
            song = songs.get(a.target_id)
            if song:
                d["target_name"]   = song.title
                d["target_artist"] = song.artist.name
                d["target_cover"]  = song.album.cover_url if song.album else None
                d["target_url"]    = f"/songs/{song.id}"
        elif a.target_type == "user" and a.target_id:
            u = users.get(a.target_id)
            if u:
                d["target_name"] = u.username
                d["target_url"]  = f"/users/{u.username}"
        result.append(d)
    return result
