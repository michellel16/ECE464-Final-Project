import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Load .env from the project root (two levels up from this file)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_ROOT, ".env"))

DATABASE_URL = os.environ["DATABASE_URL"]  # required — set in .env

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # detect stale connections
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
