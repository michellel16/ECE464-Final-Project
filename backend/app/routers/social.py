from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..auth import get_current_user
from .users import _enrich_activities

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/feed")
def get_feed(
    skip: int = 0, limit: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    following_ids = [current_user.id]

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
