# Tunelog

Tunelog is a music cataloging and sharing platform with Spotify integration. Users can review albums and songs, build curated lists, follow friends, and discover new music.

---

## Links

|                    | |
|--------------------|---|
| **Live Web App**   | *https://ece-464-tunelog.vercel.app/* |
| **Demo Video**     | *https://drive.google.com/file/d/1w9E6hySElTZh-P_e7pXgrmQBR8VdJFby/view?usp=sharing* |
| **Final Write-up** | [WRITEUP.md](./WRITEUP.md) |

---

## Tech Stack

| Layer                     | Technology                            |
|---------------------------|---------------------------------------|
| Frontend                  | React 18, Vite, Tailwind CSS          |
| Backend                   | FastAP, SQLAlchemy, Alembic           |
| Database                  | PostgreSQL w/ Supabase, pgvector      |
| Auth                      | Supabase                              |
| Server Hosting            | Railway                               |
| Frontend / Client Hosting | Vercel                                |
| Third-Party App           | Spotify Web API, OpenAI Embeddings API |

---

## Local Development

### Prerequisites

- Python 3.11+ w/ UV
- Node.js 18+
- PostgreSQL database (local or Supabase)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ECE464-Final-Project.git
cd ECE464-Final-Project
```

### 2. Set up environment variables

Copy the example and fill in the environment variables:

```bash
cp .env.example .env
```
- `DATABASE_URL` (PostgreSQL connection string)
- `SUPABASE_URL` (Supabase project URL)
- `SECRET_KEY`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

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

The backend will be hosted on `http://localhost:8000`. The seed data (artists, albums, songs, demo user) loads automatically on the first startup.

### 6. Set up the frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The app will be hosted on `http://localhost:5173`. Vite dev server proxies `/api` and `/static` to `localhost:8000` so no CORS configuration is needed for local development.

### 7. Enable semantic search

Add the `OPENAI_API_KEY` to `.env`. After the backend starts, backfill the vector indexes with the API:

```bash
curl -X POST http://localhost:8000/api/search/backfill
```

### 8. Enable Spotify integration

Add `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/api/spotify/callback` to `.env`.

See [WRITEUP.md](./WRITEUP.md#architecture) for the architecture setup.

### 9. Login with sample account
Demo account: **musiclover / password123**


---
## Database Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for all schema changes.

```bash
# Apply all migrations
uv run alembic upgrade head

# Roll back migration
uv run alembic downgrade base

# Check current revision
uv run alembic current

# Generate new migration after model changes
uv run alembic revision --autogenerate -m "description"
```
