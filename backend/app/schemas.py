from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Genre ────────────────────────────────────────────────────────────────────

class Genre(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


# ── Artist ───────────────────────────────────────────────────────────────────

class ArtistSummary(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    model_config = {"from_attributes": True}


class Artist(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    image_url: Optional[str] = None
    formed_year: Optional[int] = None
    country: Optional[str] = None
    genres: List[Genre] = []
    model_config = {"from_attributes": True}


# ── Album ────────────────────────────────────────────────────────────────────

class AlbumSummary(BaseModel):
    id: int
    title: str
    artist_id: int
    cover_url: Optional[str] = None
    release_date: Optional[str] = None
    model_config = {"from_attributes": True}


class Album(BaseModel):
    id: int
    title: str
    artist_id: int
    release_date: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    artist: Optional[ArtistSummary] = None
    genres: List[Genre] = []
    average_rating: Optional[float] = None
    review_count: Optional[int] = None
    model_config = {"from_attributes": True}


# ── Song ─────────────────────────────────────────────────────────────────────

class SongSummary(BaseModel):
    id: int
    title: str
    track_number: Optional[int] = None
    duration_seconds: Optional[int] = None
    model_config = {"from_attributes": True}


class Song(BaseModel):
    id: int
    title: str
    artist_id: int
    album_id: Optional[int] = None
    duration_seconds: Optional[int] = None
    track_number: Optional[int] = None
    artist: Optional[ArtistSummary] = None
    album: Optional[AlbumSummary] = None
    average_rating: Optional[float] = None
    review_count: Optional[int] = None
    model_config = {"from_attributes": True}


# ── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_private: Optional[bool] = None


class User(BaseModel):
    id: int
    username: str
    email: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    is_private: bool = False
    model_config = {"from_attributes": True}


# ── Review ───────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    text: Optional[str] = None
    rating: float


class Review(BaseModel):
    id: int
    user_id: int
    song_id: Optional[int] = None
    album_id: Optional[int] = None
    text: Optional[str] = None
    rating: float
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Lists ────────────────────────────────────────────────────────────────────

class ListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    list_type: str = "custom"
    is_public: bool = True


class ListItemCreate(BaseModel):
    song_id: Optional[int] = None
    album_id: Optional[int] = None
    notes: Optional[str] = None


# ── Auth ─────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
