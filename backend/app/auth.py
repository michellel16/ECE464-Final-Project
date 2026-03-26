import os
from typing import Optional

import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

_pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)

from . import models
from .database import get_db

SECRET_KEY = os.environ.get("SECRET_KEY", "tunelog-dev-secret-change-in-production")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
ALGORITHM = "HS256"  # kept for Spotify state JWTs

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        resp = httpx.get(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
        _jwks_cache = resp.json()
    return _jwks_cache


def verify_supabase_token(token: str) -> dict:
    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "RS256")

        key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == kid),
            jwks["keys"][0] if jwks.get("keys") else None,
        )
        if key is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        payload = jwt.decode(token, key, algorithms=[alg], options={"verify_aud": False})
        return payload
    except JWTError as e:
        print(f"[JWT ERROR] {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    payload = verify_supabase_token(token)
    supabase_id: str = payload.get("sub")
    if not supabase_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.supabase_id == supabase_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[models.User]:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
