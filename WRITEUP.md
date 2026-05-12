# Final Write-Up

---

## Mission

Tunelog is a catalog for music, that allows users to log what they've heard, write and share reviews, build curated lists, follow people with similar interests, and discover music that matches their taste.

The core original problem is that there are few updated social platforms that centers around curation and reviewing of music. Tunelog solves this problem by offering a review and rating system, collaborative lists, and a semantic search engine that understands mood.

---

## Schema

The database has **16 application tables** and **2 association tables**, which are managed through Alembic. Full definitions: [`backend/app/models.py`](./backend/app/models.py)

### Core Music Catalog

| Table | Purpose                                                                                     |
|---|---------------------------------------------------------------------------------------------|
| `artists` | Artist profiles - name, bio, Spotify ID, 1536-dim embedding                                 |
| `albums` | Albums - title, release date, cover, Spotify ID, 1536-dim embedding                         |
| `songs` | Tracks - duration, track number, Spotify preview URL, audio feature floats, 1536-dim embedding |
| `genres` | Genre tags (e.g. Hip-Hop, Pop, Rock)                                                        |
| `artist_genre` | Many-to-many linking artists to genres                                                     |
| `album_genre` | Many-to-many linking albums to genres                                                       |

### Users and Social Activity

| Table | Purpose                                                                                                        |
|---|----------------------------------------------------------------------------------------------------------------|
| `users` | Accounts - Supabase ID, username, email, avatar, Spotify OAuth tokens, taste embedding, music preferences JSON |
| `user_follows` | Directed follow edges (follower_id → followed_id)                                                              |
| `follow_requests` | Pending follow requests for private accounts                                                                   |
| `activities` | Activity feed (review created, list created, user followed etc.)                                               |
| `notifications` | In-app notifications (new follower, list collaboration invite, etc.)                              |

### Reviews and Album/Song Status Tracking

| Table | Purpose                                                   |
|---|-----------------------------------------------------------|
| `reviews` | 0.5–5.0 star reviews, optional text                       |
| `review_likes` | Likes on a review                          |
| `user_album_statuses` | Per-user album: `listened`, `want_to_listen`, `favorites` |
| `user_song_statuses` | Per-user song: `listened`, `want_to_listen`, `favorites`  |

### Curated Lists

| Table | Purpose                                                                                    |
|---|--------------------------------------------------------------------------------------------|
| `lists` | Named collections - type, visibility, cover image, folder group                            |
| `list_items` | Songs added to list                                                                        |
| `list_members` | Collaborators on a list as (`viewer` or `editor`), invite status (`pending` or `accepted`) |
| `list_likes` | Likes on public lists                                                                      |
| `user_recommendations` | Song and album recommendations between users                                               |

### Key Relationships

```
artists ──< albums ──< songs
   │           │
   └── genres ─┘  (Many-to-many via artist_genre, album_genre)

users ──< reviews ──> albums / songs
users ──< lists ──< list_items ──> albums / songs
users ──< list_members ──> lists
users ──< user_follows ──> users
users ──< notifications
users ──< user_recommendations ──> users
```

Schema: [`backend/app/models.py`](./backend/app/models.py)

Migration History: [`alembic/versions/`](./alembic/versions/)

---

## Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────┐
│                  User's Browser                 │
│          React 18 + Vite + Tailwind CSS         │
│              (hosted on Vercel)                 │
└────────────────────┬────────────────────────────┘
                     │ HTTPS (axios, Bearer JWT)
                     │ VITE_API_BASE_URL
                     ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                    │
│         SQLAlchemy ORM + Alembic                │
│             (hosted on Railway)                 │
│                                                 │
│  Routers: auth, users, music, lists, social,    │
│           search, stats, spotify, charts,       │
│           recommendations, notifications        │
└──────┬──────────────┬────────────────┬──────────┘
       │              │                │
       ▼              ▼                ▼
┌────────────┐  ┌──────────────┐  ┌─────────────┐
│ PostgreSQL │  │ Spotify API  │  │  OpenAI API │
│ (Supabase) │  │ (Web API +   │  │ (text-      │
│            │  │  OAuth 2.0)  │  │  embedding- │
│ pgvector   │  └──────────────┘  │  3-small)   │
│ extension  │                    └─────────────┘
└────────────┘

┌─────────────────────────────────────────────────┐
│                Supabase Auth                    │
│   signUp / signIn / password reset / JWKS       │
│   JWT issued to browser, validated by backend   │
└─────────────────────────────────────────────────┘
```

### Authentication Flow

1. User signs in via `@supabase/supabase-js` in the browser. Supabase returns a signed JWT.
2. The frontend sets an API request token.
3.  FastAPI backend fetches Supabase's JWKS endpoint and validates the RS256 signature.
4. On first login, the backend creates a `users` row linked to the Supabase user ID. All subsequent requests look up the user by the ID.

### Database Seeding

Artists, albums, songs, album covers, genres, and audio clips can be imported using the **Spotify Web API** with client-credentials auth. If an artist or album is missing a usable image, the startup job fetches it from Spotify and persists the URL. This runs in parallel so it doesn't block the server from accepting requests.

When a user imports a track or artist, the backend will embed the new content in the background without blocking the response. The task embeds a text representation of the song (title, artist, genres, audio feature summary) and stores the resulting vector on `songs.embedding`, making the track searchable via semantic search.

---

## Key Queries

### 1. Creating a review

When a user submits a review for an album or song, the backend does an upsert, an update if they've reviewed it before or an insert. This triggers a background re-embedding for future semantic search.

```python
existing = db.query(models.Review).filter_by(
    user_id=current_user.id, album_id=album_id
).first()

if existing:
    existing.text   = review.text
    existing.rating = review.rating
    db.commit()
else:
    r = models.Review(
        user_id=current_user.id, album_id=album_id,
        text=review.text, rating=review.rating
    )
    db.add(r)
    db.add(models.Activity(
        user_id=current_user.id, action_type="reviewed_album",
        target_type="album", target_id=album_id,
        meta=f'{{"rating":{review.rating}}}',
    ))
    db.commit()

background_tasks.add_task(reembed_album_bg, album_id)
```

`Activity` is only written upon the first review and not edited reviews, so the activity feed isn't cluttered. The background re-embed keeps the album's semantic vector up to date as reviews accumulate.

**Indexing Strategy:** The upsert lookup uses a composite index on `reviews.(user_id, album_id)` rather than scanning the whole table. 

---

### 2. Following a user with a private account

The follow system depends on whether the user's account is private. Public accounts get an immediate follow, an activity record, and a notification. Private accounts instead create a `follow_requests` and notify the target user to approve or deny the request.

```python
if target.is_private:
    db.add(models.FollowRequest(
        requester_id=current_user.id, target_id=target.id
    ))
    db.add(models.Notification(
        user_id=target.id, type="follow_request",
        from_user_id=current_user.id,
    ))
else:
    db.add(models.UserFollow(
        follower_id=current_user.id, followed_id=target.id
    ))
    db.add(models.Activity(
        user_id=current_user.id, action_type="followed",
        target_type="user", target_id=target.id,
    ))
    db.add(models.Notification(
        user_id=target.id, type="new_follower",
        from_user_id=current_user.id,
    ))
db.commit()
```

**Indexing Strategy:** The lookup for who the user is following and the user's followers use index scans with composite key `user_follows.(follower_id, followed_id)`. This is the same for `follow_requests.(requester_id, target_id)`.

---

### 3. Adding an item to a list (role-based access control)

Before inserting an item into a list, the backend checks whether the user is the list owner or a collaborator. Unauthenticated users are blocked from accessing the list and viewers are blocked from editing the list.

```python
def _is_editor(db, lst, user_id) -> bool:
    if lst.user_id == user_id:
        return True
    return db.query(models.ListMember).filter_by(
        list_id=lst.id, user_id=user_id,
        role="editor", status="accepted"
    ).first() is not None

# In the endpoint:
if not _is_editor(db, lst, current_user.id):
    raise HTTPException(status_code=403, detail="Editor access required")

db.add(models.ListItem(
    list_id=lst.id, song_id=song_id, album_id=album_id, notes=notes
))
db.commit()
```

The `status="accepted"` filter in `_is_editor` makes sure that users with pending collaboration invites cannot write to the list.

**Indexing Strategy:** The access check is a single index lookup with composite key `list_members.(list_id, user_id)`.

---


## Complexity Component: Semantic Vibe Search with Multi-Level Fallback

The complexity component of Tunelog is implementing semantic search and a similarity engine, which allows users to be recommended or find songs and artists by mood or feel rather than title or artist name (ex: melancholy bedroom indie).

### How it works

1. **Embedding generation.** When content is added to the catalog (seed data, Spotify import, or review creation), the backend calls OpenAI's `text-embedding-3-small` to embed a rich text representation of the item — for an album: title + artist + genres + review excerpts. For a user's taste profile: their top-reviewed artists + genre preferences + stated interests in free text. These 1536-float vectors are stored in the `embedding` column on `artists`, `albums`, `songs`, and `users`.

2. **Stored vs. live embeddings.** Search queries embed the user's natural-language query at query time (one OpenAI call per search), then compare against stored embeddings using pgvector's HNSW index. No per-item OpenAI call at query time — only the query string is embedded live.

3. **Connection pool discipline.** The FastAPI endpoint opens the DB session *after* the OpenAI call returns. This prevents a slow or rate-limited OpenAI request from holding a SQLAlchemy pool connection open for the duration.

4. **Multi-level fallback for similarity.** The `/api/search/similar` endpoint, used on artist/album/song pages to show "More like this," implements a four-level fallback strategy so every item always returns results — even before embeddings have been generated:

   - **Level 1 — Embedding similarity:** pgvector cosine distance query against stored vectors (most semantically accurate)
   - **Level 2 — Genre overlap:** SQL `COUNT(*) ... GROUP BY ... ORDER BY shared DESC` using the genre association tables, with a keyword normalization map that handles Spotify's verbose genre slugs (e.g. "uk neo soul" → R&B)
   - **Level 3 — Spotify Related Artists API:** calls Spotify's `related-artists` endpoint (which uses their own internal similarity graph), then resolves Spotify IDs to local DB rows
   - **Level 4 — Top-rated globally:** guaranteed fallback that always returns something

5. **Personalized recommendations.** Beyond search, the `/api/recommendations/me` endpoint builds a **taste embedding** for the user from their activity (weighted review scores + status flags + music preference text), stores it on `users.taste_embedding`, and uses pgvector to find albums whose embeddings are closest to the user's taste vector. A hash of the taste inputs (`taste_profile_hash`) prevents re-embedding when nothing has changed.

6. **Backfill endpoint.** `POST /api/search/backfill` embeds all unindexed content in batches of 5, with a 1-second delay between batches to respect OpenAI's rate limit. It uses `asyncio.gather` within each batch for concurrency.

---

## The Journey

### What worked well

**FastAPI + SQLAlchemy** was a strong pairing. FastAPI's automatic OpenAPI docs made it easy to test endpoints in isolation, and SQLAlchemy's relationship system handled the complex joins (reviews → albums → artists → genres) cleanly once the models were right.

**Alembic** paid off immediately. The schema evolved significantly over 16 migrations — adding Spotify columns, pgvector embeddings, the list collaboration system, and notifications. Being able to roll back and replay any point in the schema history was essential when migrations needed fixing.

**pgvector on Supabase** was simpler to set up than expected. Supabase pre-installs the extension, so enabling it was a single `CREATE EXTENSION IF NOT EXISTS vector` in the migration, and the HNSW index creation just worked.

### What was harder than expected

**Spotify's OAuth round-trip** required careful state management. The backend signs a short-lived JWT (not the user's session JWT — a separate one with `typ=spotify_state`) to pass the `user_id` through Spotify's callback redirect without storing server-side state. Getting the redirect chain right across localhost ↔ Railway ↔ Spotify ↔ Vercel took several iterations.

**Connection pooling with Supabase** had a surprising edge case: the transaction-mode pooler (port 6543) doesn't support `SET` commands, which the SQLAlchemy `connect` event used to disable statement timeouts. Detecting the port in the URL and switching to `NullPool` for the transaction pooler, while using a bounded pool for session-mode connections, resolved this.

**The list collaboration UX** grew more complex than anticipated. What started as simple sharing became an invite/accept flow with role-based access control, pending states, in-app notifications, owner transfer protection, and deep-linking to the Collab tab via query parameters.

### AI-assisted development

Claude was used throughout this project for boilerplate acceleration (Alembic migration templates, Pydantic schema generation, Tailwind component styling) and for debugging non-obvious issues (the pgvector connection pool edge case, the Spotify state JWT design). The most valuable use was iterating on the multi-level similarity fallback logic — describing the desired behavior in natural language and refining the SQL queries and fallback ordering together. The design decisions, architecture choices, and all debugging were done collaboratively with Claude Code rather than delegated to it.

---

## Scaling

The current single-instance Railway + Supabase free-tier architecture would break down around 10,000 concurrent users. Here is how to evolve it to 1 million active users:

### Database

- **Read replicas.** The vast majority of requests (search, browse, feed) are reads. Supabase supports read replicas; route all `SELECT` queries to a replica pool and keep writes on the primary.
- **Connection pooling via PgBouncer.** At scale, SQLAlchemy's connection pool per dyno multiplies dangerously. Route all connections through PgBouncer (Supabase includes this via the transaction pooler) and reduce `pool_size` per instance.
- **Partition `reviews` and `activities`.** These are the highest-write tables. Partition by `user_id` hash range to keep index sizes manageable. At 1M users with 10 reviews each, that's 10M rows — still fine — but `activities` could be 100M+.
- **Vector index sharding.** The HNSW index on `songs.embedding` with millions of tracks would need a distributed ANN solution (e.g. Weaviate, Qdrant, or pgvector with partitioned tables).

### Backend

- **Horizontal scaling.** Railway supports multiple replicas. The FastAPI app is stateless (no in-memory session state; Supabase Auth handles tokens), so scaling out is straightforward.
- **Background job queue.** The current `asyncio.create_task` approach for embedding generation and MusicBrainz backfill is fire-and-forget within a single process. At scale this should move to a proper job queue (Celery + Redis, or a managed service like Railway's worker service) to survive restarts and handle retry logic.
- **CDN for static assets.** User-uploaded avatars and list covers are currently served from Railway's filesystem (ephemeral). Move to Supabase Storage or S3 + CloudFront. This also fixes the data-loss-on-redeploy issue.
- **Cache hot reads.** Album pages and the global charts are read-heavy and change infrequently. A Redis layer (or Supabase's edge functions with KV) caching the top 1000 albums' review aggregates would dramatically reduce DB load.

### Frontend

- **Vercel's edge network** already handles CDN and global distribution. No changes needed for the static bundle.
- **Infinite scroll and cursor pagination.** The current `LIMIT 8` / `LIMIT 100` patterns work at small scale but need cursor-based pagination (`WHERE id > :last_seen_id ORDER BY id`) for feeds and lists as data grows.
