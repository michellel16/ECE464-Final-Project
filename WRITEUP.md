# Final Write-Up

---

## Mission

Tunelog is a catalog for music, that allows users to log what they've listened to, write and share reviews, build curated lists, follow people with similar interests, and discover music that matches their taste.

The core original problem is that there are few updated social platforms that centers around curation and reviewing of music. Tunelog solves this problem by offering a review and rating system, collaborative lists, and a semantic search engine that understands mood.

---

## Schema

The database has 18 tables that are managed through Alembic. The table definitions are in [`backend/app/models.py`](./backend/app/models.py)

### Music Catalog

| Table | Purpose/Attributes                                                               |
|---|----------------------------------------------------------------------------------|
| `artists` | Name, bio, Spotify ID, 1536-dim embedding                                        |
| `albums` | Title, release date, cover, Spotify ID, 1536-dim embedding                       |
| `songs` | Duration, track number, Spotify preview URL, audio feature floats, 1536-dim embedding |
| `genres` | Genre tags                                                                       |
| `artist_genre` | Many-to-many relation for artists to genres                                      |
| `album_genre` | Many-to-many relation for albums to genres                                       |

### Users and Social Activity

| Table | Purpose/Attributes                                                                                  |
|---|-----------------------------------------------------------------------------------------------------|
| `users` | Supabase ID, username, email, avatar, Spotify OAuth tokens, taste embedding, music preferences JSON |
| `user_follows` | Follows (follower_id → followed_id)                                                                 |
| `follow_requests` | Pending follow requests for private accounts                                                        |
| `activities` | Activity feed (review created, list created, user followed etc.)                                    |
| `notifications` | Notifications (new follower, list collaboration invite, etc.)                                       |

### Reviews and Album/Song Status Tracking

| Table | Purpose/Attributes                                                    |
|---|-----------------------------------------------------------|
| `reviews` | 0.5–5.0 star reviews, optional text                       |
| `review_likes` | Likes on a review                          |
| `user_album_statuses` | Per-user album: `listened`, `want_to_listen`, `favorites` |
| `user_song_statuses` | Per-user song: `listened`, `want_to_listen`, `favorites`  |

### Curated Lists

| Table | Purpose/Attributes                                                                         |
|---|--------------------------------------------------------------------------------------------|
| `lists` | Type, visibility, cover image, folder group                                                |
| `list_items` | Songs added to list                                                                        |
| `list_members` | Collaborators on a list as (`viewer` or `editor`), invite status (`pending` or `accepted`) |
| `list_likes` | Likes on public lists                                                                      |
| `user_recommendations` | Song and album recommendations between users                                               |

### Key Relationships
-< represents one to many (1:N), -> represents many to one, -- represents many to many (M:N)

```
artists ──< albums ──< songs
   │           │
   └── genres ─┘

- users ─< reviews ─> albums / songs
- users ─< lists ─< list_items ─> albums / songs
- users ─< list_members ─> lists
- users ─< user_follows ─> users
- users ─< notifications
- users ─< user_recommendations ─> users
```

Schema: [`backend/app/models.py`](./backend/app/models.py)

Migration History: [`alembic/versions/`](./alembic/versions/)

---

## Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────┐                     ┌─────────────────────────────────────────────────┐
│                Browser                  │  Auth               │                Supabase Auth                    │
│     React 18 + Vite + Tailwind CSS      │-------------------> │   signUp, sign in, password reset, etc.         │
│         (hosted on Vercel)              │                     │   JWT issued to browser, validated by backend   │
└─────────────────────────────────────────┘                     └─────────────────────────────────────────────────┘
                     | HTTPS Request                                                    |
                     |                                                                  |
                     V                                                                  |
┌─────────────────────────────────────────┐                                             |
│              FastAPI Backend            │          JWT auth                           |                                      
│        w/ SQLAlchemy + Alembic          │----------------------------------------------
│                (Railway)                │
└─────────────────────────────────────────┘
       |              |                |
       V              V                V
┌────────────┐  ┌──────────────┐  ┌─────────────┐
│ PostgreSQL │  │ Spotify API  │  │ OpenAI API  │
│ (Supabase) │  │ (Web API +   │  │ (text-      │
│            │  │  OAuth)      │  │  embedding- │
│ pgvector   │  └──────────────┘  │  3-small)   │
│ extension  │                    └─────────────┘
└────────────┘
```

### Authentication Flow

1. User signs in the browser and Supabase returns a signed JWT.
2. Frontend sets an API request token.
3.  FastAPI backend fetches Supabase's JWKS endpoint and validates the signature.
4. At first login, the backend creates a `users` row linked to the Supabase user ID. All following requests will look up the user by the ID.

### Database Seeding / External Data

Artists, albums, songs, album covers, genres, and audio clips can be imported using the **Spotify Web API** with client-credentials auth. If an artist or album is missing a usable image, the startup job fetches it from Spotify and persists the URL. This runs in parallel so it doesn't block the server from accepting requests.

---

## Key Queries

### 1. Creating a review

When a user submits a review for an album or song, the backend does an upsert if they've reviewed it before or an insert otherwise. This triggers a background re-embedding task.

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

if not _is_editor(db, lst, current_user.id):
    raise HTTPException(status_code=403, detail="Editor access required")

db.add(models.ListItem(
    list_id=lst.id, song_id=song_id, album_id=album_id, notes=notes
))
db.commit()
```

The `status="accepted"` filter makes sure that users with pending collaboration invites can't write to the list.

**Indexing Strategy:** The access check is a single index lookup with composite key `list_members.(list_id, user_id)`.

---


## Complexity Component: Semantic Search w/ Pgvector and OpenAI Embeddings
The complexity component is implementing semantic search, which recommends users songs, artists, and albums by mood or feel rather than title or artist name (ex: melancholy bedroom indie) This goes for the home page recommendations and search output.

When content is added to the catalog (seed data, Spotify import, or review), the backend calls OpenAI's `text-embedding-3-small` API to embed a text representation of the item. The vectors are stored in the `embedding` column on `artists`, `albums`, `songs`, and `users`. This occurs as a background task.

When a user runs a semantic search, their query is embedded at query time with an OpenAI API call. The query vector is then compared against stored embeddings. 

For the recommendations, a taste profile embedding is built for the user from activity (review scores, music preferences, etc). Pgvector is used to find albums, artists, and songs whose embeddings are closest to the user's taste vector. 

Updating the recommendations does not wait for OpenAI API calls. It checks to see if the SHA-256 fingerprint of the user’s relevant activity has changed, before calling the API to regenerate the taste embedding. Then, a weighted average of the vectors are calculated. A hash of inputs prevents re-embedding when nothing has changed.

A backfill API is also used to embed any unindexed content in batches.

---

## The Journey

Overall, the stack allowed for easy implementation of core logic. The FastAPI backend specifically made it easy to test API endpoints in isolation, while SQLAlchemy made it easy to handle queries cleanly.
Alembic was also useful in easy schema migrations and resolving issues when the schema needed to be rolled back.

Some difficulties that were encountered were OpenAI's embedding rate limits that limited search queries and recommendations updates, which required implementing a retry mechanism with exponential backoff for the embedding tasks. 

There was also difficulty with connection pooling with Supabase, as there were conflicts between the transaction-mode pooler and SQLAlchemy.

Lastly, there was difficulty in anticipating interactions between users that are standard in other web apps, with the follow system, notification system, and collaborative lists.
Specifically, the list collaboration system grew more complex than anticipated. Initially, it was simple list sharing, but was expanded to having a invite/accept basis with role-based access control, pending states, and notifications.


### AI-Assisted Development

Claude was useful for implementing boilerplate code, with Alembic migration templates, rough architecture and API design, rough schema generation, CSS styling, etc. Claude was also useful in debugging, such as the pgvector connection pool error, conflicts with Spotify state JWT, etc. 

Claude was used to implement multi-level fallback logic when attempting to catch several issues, specifically with the OpenAI API rate limiting.

---

## Scaling

To evolve this architecture to support one million users, for the database layer, read replica pools for read queries can be used to handle increased request load. 
In addition, partitioning the highest-write tables, reviews and activities, by user id hash range can keep index sizes manageable. 

For the backend, the OpenAI embedding calls are currently extremely rate-limited, which affects the runtime of the search queries and the accuracy of recommendations. Ideally, for full-scale production, the web app would need a much higher rate limit or custom embedding solution.

The backend can be horizontally scaled with multiple servers behind a load balancer, since the webapp is stateless. In addition, the pictures that users can upload (list cover images, profile pictures, profile backgrounds) are currently stored on the Railway filesystem but should be moved to a storage system like Amazon S3. Lastly, adding a caching layer with Redis for things like album pages and the discover page would reduce database load.
