#!/bin/bash
echo "Waiting for database to be ready..."
sleep 5

echo "Running migrations..."
for i in $(seq 1 20); do
    uv run alembic upgrade head && break
    echo "Migration attempt $i failed, retrying in 10s..."
    sleep 10
done

echo "Starting server..."
exec uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
