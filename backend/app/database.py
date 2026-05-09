import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# Load .env from the project root (two levels up from this file)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_ROOT, ".env"))

# APP_DATABASE_URL takes priority (use this on Railway to avoid the auto-injected internal URL).
# Falls back to DATABASE_URL for local dev.
print("[db] env keys:", sorted(os.environ.keys()))
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

_CONNECT_ARGS = {"options": "-c statement_timeout=0", "connect_timeout": 5}

if _using_supabase_pooler:
    engine = create_engine(DATABASE_URL, poolclass=NullPool, connect_args=_CONNECT_ARGS)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=8,    # hard cap: 13 total, leaves 2 for Supabase admin connections
        pool_timeout=10,   # fail fast instead of waiting 30 s for a free slot
        pool_recycle=1800, # recycle idle connections every 30 min
        connect_args=_CONNECT_ARGS,
    )


@event.listens_for(engine, "connect")
def _disable_statement_timeout(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout = 0")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
