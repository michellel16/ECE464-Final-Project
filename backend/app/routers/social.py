from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..auth import get_current_user
from .users import _enrich_activities, _user_out

router = APIRouter(prefix="/api/social", tags=["social"])


# ── Activity feed ─────────────────────────────────────────────────────────────

@router.get("/feed")
def get_feed(
    skip: int = 0, limit: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Include own activity + everyone you follow
    following_ids = [f.followed_id for f in current_user.following]
    following_ids.append(current_user.id)

    one_month_ago = datetime.utcnow() - timedelta(days=30)
    activities = (
        db.query(models.Activity)
        .filter(
            models.Activity.user_id.in_(following_ids),
            models.Activity.created_at >= one_month_ago,
        )
        .order_by(models.Activity.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return _enrich_activities(activities, db)


# ── Recommendations ───────────────────────────────────────────────────────────

@router.get("/recommendations/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    count = (
        db.query(func.count(models.UserRecommendation.id))
        .filter_by(recipient_id=current_user.id, is_read=False)
        .scalar() or 0
    )
    return {"count": count}


@router.get("/recommendations")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    recs = (
        db.query(models.UserRecommendation)
        .filter_by(recipient_id=current_user.id)
        .order_by(models.UserRecommendation.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for r in recs:
        row = {
            "id": r.id,
            "sender_username": r.sender.username,
            "sender_avatar_url": r.sender.avatar_url,
            "note": r.note,
            "is_read": r.is_read,
            "created_at": r.created_at,
        }
        if r.song:
            row["song"] = {
                "id": r.song.id,
                "title": r.song.title,
                "artist": r.song.artist.name if r.song.artist else None,
                "cover_url": r.song.album.cover_url if r.song.album else None,
            }
        if r.album:
            row["album"] = {
                "id": r.album.id,
                "title": r.album.title,
                "artist": r.album.artist.name if r.album.artist else None,
                "cover_url": r.album.cover_url,
            }
        result.append(row)
    return result


@router.post("/recommend")
def send_recommendation(
    recipient_username: str = Body(...),
    song_id: Optional[int] = Body(None),
    album_id: Optional[int] = Body(None),
    note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not song_id and not album_id:
        raise HTTPException(status_code=400, detail="Must specify song_id or album_id")

    recipient = db.query(models.User).filter(models.User.username == recipient_username).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    if recipient.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot recommend to yourself")

    rec = models.UserRecommendation(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        song_id=song_id,
        album_id=album_id,
        note=note.strip() if note else None,
    )
    db.add(rec)
    db.commit()
    return {"message": f"Recommendation sent to {recipient_username}"}


@router.post("/recommendations/{rec_id}/read")
def mark_read(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rec = db.query(models.UserRecommendation).filter_by(
        id=rec_id, recipient_id=current_user.id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    rec.is_read = True
    db.commit()
    return {"message": "Marked as read"}


@router.post("/recommendations/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.UserRecommendation).filter_by(
        recipient_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All marked as read"}
