"""One-time script to drop all tables so migrations can run clean."""
from backend.app.database import engine, Base
from backend.app import models  # noqa: F401 — registers all ORM models

Base.metadata.drop_all(engine)
print("All tables dropped. Now run: uv run alembic upgrade head")
