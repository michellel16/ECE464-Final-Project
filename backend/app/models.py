
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from .database import Base

# ── Association tables ──────────────────────────────────────────────────────

artist_genre = Table(
    "artist_genre", Base.metadata,
    Column("artist_id", Integer, ForeignKey("artists.id"), primary_key=True),
    Column("genre_id",  Integer, ForeignKey("genres.id"),  primary_key=True),
)

album_genre = Table(
    "album_genre", Base.metadata,
    Column("album_id", Integer, ForeignKey("albums.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)


# ── Core models ─────────────────────────────────────────────────────────────

class Genre(Base):
    __tablename__ = "genres"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    artists = relationship("Artist", secondary=artist_genre, back_populates="genres")
    albums  = relationship("Album",  secondary=album_genre,  back_populates="genres")


class Artist(Base):
    __tablename__ = "artists"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False, index=True)
    bio         = Column(Text,        nullable=True)
    image_url   = Column(String,      nullable=True)
    formed_year = Column(Integer,     nullable=True)
    country     = Column(String(50),  nullable=True)

    genres  = relationship("Genre",  secondary=artist_genre, back_populates="artists")
    albums  = relationship("Album",  back_populates="artist")
    songs   = relationship("Song",   back_populates="artist")


class Album(Base):
    __tablename__ = "albums"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False, index=True)
    artist_id    = Column(Integer, ForeignKey("artists.id"), nullable=False)
    release_date = Column(String(20), nullable=True)
    cover_url    = Column(String,     nullable=True)
    description  = Column(Text,       nullable=True)

    artist        = relationship("Artist",          back_populates="albums")
    genres        = relationship("Genre",           secondary=album_genre, back_populates="albums")
    songs         = relationship("Song",            back_populates="album", order_by="Song.track_number")
    reviews       = relationship("Review",          back_populates="album")
    user_statuses = relationship("UserAlbumStatus", back_populates="album")
    list_items    = relationship("ListItem",        back_populates="album")


class Song(Base):
    __tablename__ = "songs"
    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(200), nullable=False, index=True)
    artist_id        = Column(Integer, ForeignKey("artists.id"), nullable=False)
    album_id         = Column(Integer, ForeignKey("albums.id"),  nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    track_number     = Column(Integer, nullable=True)

    artist        = relationship("Artist",         back_populates="songs")
    album         = relationship("Album",          back_populates="songs")
    reviews       = relationship("Review",         back_populates="song")
    user_statuses = relationship("UserSongStatus", back_populates="song")
    list_items    = relationship("ListItem",       back_populates="song")


# ── User ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, index=True, nullable=False)
    email           = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    bio             = Column(Text,   nullable=True)
    avatar_url      = Column(String, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    is_active       = Column(Boolean, default=True)

    reviews       = relationship("Review",          back_populates="user")
    lists         = relationship("List",            back_populates="user")
    activities    = relationship("Activity",        back_populates="user")
    song_statuses = relationship("UserSongStatus",  back_populates="user")
    album_statuses= relationship("UserAlbumStatus", back_populates="user")
    followers     = relationship("UserFollow", foreign_keys="UserFollow.followed_id",  back_populates="followed")
    following     = relationship("UserFollow", foreign_keys="UserFollow.follower_id",  back_populates="follower")


# ── Social ──────────────────────────────────────────────────────────────────

class UserFollow(Base):
    __tablename__ = "user_follows"
    follower_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    followed_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")


class Activity(Base):
    __tablename__ = "activities"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(60), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id   = Column(Integer,    nullable=True)
    meta        = Column(Text,       nullable=True)  # JSON
    created_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activities")


# ── Reviews ─────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"),   nullable=False)
    song_id    = Column(Integer, ForeignKey("songs.id"),   nullable=True)
    album_id   = Column(Integer, ForeignKey("albums.id"),  nullable=True)
    text       = Column(Text,  nullable=True)
    rating     = Column(Float, nullable=False)          # 0.5 – 5.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user  = relationship("User",  back_populates="reviews")
    song  = relationship("Song",  back_populates="reviews")
    album = relationship("Album", back_populates="reviews")


# ── Lists ───────────────────────────────────────────────────────────────────

class List(Base):
    __tablename__ = "lists"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text,    nullable=True)
    list_type   = Column(String(50), default="custom")   # listened | want_to_listen | favorites | custom
    is_public   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user  = relationship("User",     back_populates="lists")
    items = relationship("ListItem", back_populates="list", cascade="all, delete-orphan")


class ListItem(Base):
    __tablename__ = "list_items"
    id       = Column(Integer, primary_key=True, index=True)
    list_id  = Column(Integer, ForeignKey("lists.id"),  nullable=False)
    song_id  = Column(Integer, ForeignKey("songs.id"),  nullable=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes    = Column(Text, nullable=True)

    list  = relationship("List",  back_populates="items")
    song  = relationship("Song",  back_populates="list_items")
    album = relationship("Album", back_populates="list_items")


# ── Status tracking ─────────────────────────────────────────────────────────

class UserSongStatus(Base):
    __tablename__ = "user_song_statuses"
    user_id    = Column(Integer, ForeignKey("users.id"), primary_key=True)
    song_id    = Column(Integer, ForeignKey("songs.id"), primary_key=True)
    status     = Column(String(50), nullable=False)   # listened | want_to_listen | favorites
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="song_statuses")
    song = relationship("Song", back_populates="user_statuses")


class UserAlbumStatus(Base):
    __tablename__ = "user_album_statuses"
    user_id    = Column(Integer, ForeignKey("users.id"),  primary_key=True)
    album_id   = Column(Integer, ForeignKey("albums.id"), primary_key=True)
    status     = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user  = relationship("User",  back_populates="album_statuses")
    album = relationship("Album", back_populates="user_statuses")
