import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# Load .env from the project root (two levels up from this file)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_ROOT, ".env"))

# APP_DATABASE_URL takes priority (use this on Railway to avoid the auto-injected internal URL).
# Falls back to DATABASE_URL for local dev.
print("[db] APP_DATABASE_URL =", repr(os.environ.get("APP_DATABASE_URL")))
print("[db] DATABASE_URL =", repr(os.environ.get("DATABASE_URL")))
DATABASE_URL = os.environ.get("APP_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "On Railway: set APP_DATABASE_URL to the public Postgres URL. "
        "Locally: set DATABASE_URL in your .env file."
    )

# Supabase's transaction-mode pooler (port 6543) manages its own connection pool,
# so SQLAlchemy should not pool on top of it — use NullPool in that case.
# For session-mode (port 5432) or direct connections, use a small pool that
# stays within Supabase's free-tier limit of ~15 session connections.
_using_supabase_pooler = ":6543" in DATABASE_URL

if _using_supabase_pooler:
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=7,   # hard cap: 10 total, well within Supabase's 15-connection limit
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
