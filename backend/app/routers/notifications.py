from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _notif_out(n: models.Notification, db=None) -> dict:
    out = {
        "id": f"n_{n.id}",
        "type": n.type,
        "from_user": {
            "id": n.from_user.id,
            "username": n.from_user.username,
            "avatar_url": getattr(n.from_user, "avatar_url", None),
        } if n.from_user else None,
        "entity_type": n.entity_type,
        "entity_id":   n.entity_id,
        "is_read":     n.is_read,
        "created_at":  n.created_at,
    }
    if n.type == "review_like" and n.entity_id and db:
        review = db.query(models.Review).filter_by(id=n.entity_id).first()
        if review:
            if review.album_id:
                out["review_target"] = {"type": "album", "id": review.album_id}
            elif review.song_id:
                out["review_target"] = {"type": "song", "id": review.song_id}
    return out


def _rec_out(r: models.UserRecommendation) -> dict:
    row: dict = {
        "id":         f"rec_{r.id}",
        "type":       "recommendation",
        "from_user":  {
            "id": r.sender.id,
            "username": r.sender.username,
            "avatar_url": getattr(r.sender, "avatar_url", None),
        },
        "note":       r.note,
        "is_read":    r.is_read,
        "created_at": r.created_at,
    }
    if r.song:
        row["song"] = {
            "id":        r.song.id,
            "title":     r.song.title,
            "cover_url": r.song.album.cover_url if r.song.album else None,
        }
    if r.album:
        row["album"] = {
            "id":        r.album.id,
            "title":     r.album.title,
            "cover_url": r.album.cover_url,
        }
    return row


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notif_count = db.query(func.count(models.Notification.id)).filter_by(
        user_id=current_user.id, is_read=False
    ).scalar() or 0
    rec_count = db.query(func.count(models.UserRecommendation.id)).filter_by(
        recipient_id=current_user.id, is_read=False
    ).scalar() or 0
    return {"count": notif_count + rec_count}


@router.get("/")
def get_notifications(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notifs = (
        db.query(models.Notification)
        .options(joinedload(models.Notification.from_user))
        .filter_by(user_id=current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    recs = (
        db.query(models.UserRecommendation)
        .options(
            joinedload(models.UserRecommendation.sender),
            joinedload(models.UserRecommendation.song).joinedload(models.Song.album),
            joinedload(models.UserRecommendation.album),
        )
        .filter_by(recipient_id=current_user.id)
        .order_by(models.UserRecommendation.created_at.desc())
        .limit(limit)
        .all()
    )

    combined = [_notif_out(n, db) for n in notifs] + [_rec_out(r) for r in recs]
    combined.sort(key=lambda x: x["created_at"], reverse=True)
    return combined[:limit]


@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter_by(
        user_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.query(models.UserRecommendation).filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
