#!/bin/bash
echo "Running migrations..."
for i in 1 2 3 4 5 6 7 8 9 10; do
    uv run alembic upgrade head && break
    echo "Migration attempt $i failed, retrying in 5s..."
    sleep 5
done

echo "Starting server..."
exec uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
