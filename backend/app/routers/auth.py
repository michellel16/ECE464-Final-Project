from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from .. import models, schemas
from ..database import get_db
from ..auth import verify_supabase_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SyncRequest(BaseModel):
    username: Optional[str] = None  # required only on first sign-up


@router.post("/sync", response_model=schemas.User)
async def sync_user(
    body: SyncRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ")
    payload = await verify_supabase_token(token)
    supabase_id = payload["sub"]
    email = payload.get("email", "")

    user = db.query(models.User).filter(models.User.supabase_id == supabase_id).first()
    if user:
        user.follower_count = db.query(func.count(models.UserFollow.follower_id)).filter_by(followed_id=user.id).scalar() or 0
        user.following_count = db.query(func.count(models.UserFollow.followed_id)).filter_by(follower_id=user.id).scalar() or 0
        return user

    # First time — create profile
    if not body.username:
        raise HTTPException(status_code=400, detail="Username required for new account")
    if db.query(models.User).filter(func.lower(models.User.username) == body.username.lower()).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = models.User(
        username=body.username,
        email=email,
        supabase_id=supabase_id,
        hashed_password=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.follower_count = 0
    user.following_count = 0
    return user


@router.get("/me", response_model=schemas.User)
def get_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.follower_count = db.query(func.count(models.UserFollow.follower_id)).filter_by(followed_id=current_user.id).scalar() or 0
    current_user.following_count = db.query(func.count(models.UserFollow.followed_id)).filter_by(follower_id=current_user.id).scalar() or 0
    return current_user
