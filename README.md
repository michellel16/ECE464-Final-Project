# Tunelog

A music cataloging and sharing platform with Spotify integration. Users can review albums and songs, build curated lists, follow friends, and discover new music.

---

## Links

| | |
|---|---|
| **Live App** | *https://ece-464-tunelog.vercel.app/* |
| **Demo Video** | *(add link here)* |
| **Final Write-up** | [WRITEUP.md](./WRITEUP.md) |
| **Final Presentation** | *(add link here)* |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL (Supabase) + pgvector |
| Auth | Supabase Auth (JWT) |
| Backend Hosting | Railway |
| Frontend Hosting | Vercel |
| External APIs | Spotify Web API, OpenAI Embeddings |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- [UV](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- PostgreSQL database (local or Supabase)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ECE464-Final-Project.git
cd ECE464-Final-Project
```

### 2. Set up environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

- `DATABASE_URL` — a PostgreSQL connection string
- `SUPABASE_URL` — your Supabase project URL
- `SECRET_KEY` — any random string for development

See `.env.example` for all variables and where to find them.

### 3. Install backend dependencies

```bash
uv sync
```

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start the backend

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

The API will be `http://localhost:8000`. The seed data (artists, albums, songs, demo user) loads automatically on first startup.

Demo account: **musiclover / password123**

### 6. Set up the frontend

```bash
cd frontend
cp .env.example .env   # fill in VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
npm install
npm run dev
```

The app will be at `http://localhost:5173`. The Vite dev server proxies `/api` and `/static` to `localhost:8000` — no CORS configuration needed locally.

### 7. Enable semantic search

Add your `OPENAI_API_KEY` to `.env`, then after the backend starts, seed the vector index:

```bash
curl -X POST http://localhost:8000/api/search/backfill
```

### 8. Enable Spotify integration

Add `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/api/spotify/callback` to `.env`.

---

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for all schema changes.

```bash
# Apply all migrations
uv run alembic upgrade head

# Roll back everything
uv run alembic downgrade base

# Check current revision
uv run alembic current

# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "description"
```

---

## Deployment

See the deployment guide in [WRITEUP.md & Architecture](./WRITEUP.md#architecture) for the full cloud setup (Supabase + Railway + Vercel).
