# ☕ StudySpot – find a study cafe

A web app that helps students find study cafes by **space, busyness, distance, price and wifi**, review them,
and see which cafe their friends are studying at (opt-in check-ins, never live GPS).

| Layer    | Tech |
|----------|------|
| Backend  | Python 3.11+, Flask (app factory + blueprints), Flask-SQLAlchemy, Flask-Migrate/Alembic, psycopg 3, Flask-JWT-Extended, marshmallow |
| Database | PostgreSQL + TimescaleDB ([Tiger Cloud](https://console.cloud.timescale.com) or local Docker) |
| Frontend | Vanilla JS (ES modules), Tailwind CSS v4, Vite, Leaflet + OpenStreetMap |

```
.
├── docker-compose.yml        # local TimescaleDB (dev + test databases)
├── docker/init-test-db.sql
├── backend/
│   ├── app/
│   │   ├── __init__.py       # create_app() factory
│   │   ├── config.py         # settings from .env
│   │   ├── extensions.py     # db, migrate, jwt, cors
│   │   ├── errors.py         # consistent JSON errors
│   │   ├── models.py         # SQLAlchemy models (2 hypertables)
│   │   ├── schemas.py        # marshmallow input validation
│   │   ├── utils.py          # pagination, Haversine SQL, current user
│   │   ├── services/         # busyness/rating aggregates, friends visibility rules, check-ins
│   │   └── blueprints/       # auth, users, cafes, reviews, friends, checkins
│   ├── migrations/           # Alembic (initial migration creates the hypertables)
│   ├── tests/                # pytest (runs against a real Timescale test DB)
│   ├── seed.py               # demo data around London
│   ├── wsgi.py
│   ├── requirements.txt / requirements-dev.txt / .env.example
└── frontend/
    ├── index.html, vite.config.js
    └── src/
        ├── main.js, router.js (hash router), api.js (fetch wrapper), auth.js
        ├── components/       # navbar, map, cafe card, toast, ui helpers
        └── views/            # login, register, search, cafeDetail, writeReview, friends, settings
```

---

## 1. Prerequisites

- Python **3.11+**, Node **18+** (20+ recommended), Git
- **Either** Docker Desktop (local database) **or** a free Tiger Cloud account

## 2. Backend setup (virtual environment)

```bash
cd backend
python3 -m venv .venv            # Windows: python -m venv .venv

# Activate it (do this in every new terminal before running backend commands):
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows (PowerShell / cmd)
# (Git Bash on Windows: source .venv/Scripts/activate)

python -m pip install --upgrade pip
pip install -r requirements-dev.txt   # runtime deps + pytest

cp .env.example .env             # Windows cmd: copy .env.example .env
```

Then edit `backend/.env`:
- Set `JWT_SECRET_KEY` to a random string: `python -c "import secrets; print(secrets.token_hex(32))"`
- Set `DATABASE_URL` (see step 3).

> **Never commit `.env`.** It's in `.gitignore`. Only `.env.example` is committed.

## 3. Database

### Option A – Tiger Cloud (hosted TimescaleDB)

1. Sign up at <https://console.cloud.timescale.com> and **Create a service** (any region; the free tier is fine).
2. When the service is created, copy the **connection string** shown (you can also download it as a
   `.env`/credentials file; the password is only shown once). It looks like:
   `postgres://tsdbadmin:<password>@<id>.<project>.tsdb.cloud.timescale.com:<port>/tsdb?sslmode=require`
3. Paste it into `backend/.env` as `DATABASE_URL=...` (keep `?sslmode=require`).
   The app rewrites the scheme to use psycopg 3 automatically.
4. For tests, either point `TEST_DATABASE_URL` at a **separate** database (tests wipe it!) or use local Docker for tests.

### Option B – Local Docker (recommended for development and tests)

```bash
# from the repo root
docker compose up -d
```

This starts `timescale/timescaledb` on `localhost:5432` with user/password `studycafe`, database `studycafe`,
and also creates `studycafe_test` for pytest. The defaults in `.env.example` already point to it.

> The test database is created by `docker/init-test-db.sql` only the **first time** the volume is created.
> If you started the container before that file existed: `docker compose down -v && docker compose up -d`.

> Port 5432 already used by a local Postgres? Change the left side of `"5432:5432"` (e.g. `"5433:5432"`) and the port in `.env`.

## 4. Migrations and seed data

```bash
cd backend   # with the venv activated
flask db upgrade     # creates tables + TimescaleDB hypertables
python seed.py       # 15 London cafes, 4 users, reviews, busyness reports, friendships, check-ins
```

Demo accounts (password `password123`):

| user    | notes |
|---------|-------|
| alice   | sharing **off**, friends with bob & charlie, pending request from dana |
| bob     | sharing on, checked in at *The Reading Room* |
| charlie | sharing on, checked in at *Kings Cross Commons* |
| dana    | sharing on, has a pending request to alice |

Log in as **alice**: you'll see bob and charlie on the Friends page. Log in as **bob**: you'll see charlie but
**not** alice, because her sharing is off.

`python seed.py` wipes and re-creates all data. Busyness is time-based, so re-run it if "current busyness" looks empty later.

## 5. Run

```bash
# Terminal 1 – backend (venv activated)
cd backend
flask run                 # http://localhost:5000  (health check: /api/health)

# Terminal 2 – frontend
cd frontend
npm install               # first time only
npm run dev               # http://localhost:5173
```

Vite proxies `/api` to Flask, so no CORS setup is needed in development. If port 5173 is taken, Vite picks
the next free one (5174…).

## 6. Tests

```bash
cd backend               # venv activated, Docker DB running
pytest
```

Tests use `TEST_DATABASE_URL` (default `studycafe_test`), run the real Alembic migrations, and truncate tables
between tests. They cover auth, search filters and Haversine distance, busyness windows and time buckets,
reviews (validation, ownership, one per cafe) and **friends check-in visibility rules**.

---

## Design notes

- **Hypertables.** `checkins` and `busyness_reports` are TimescaleDB hypertables partitioned on `time`
  (created in `migrations/versions/*_initial_schema_with_hypertables.py`). TimescaleDB requires every primary
  key/unique constraint to include the time column, so these tables use composite keys
  (`(user_id, time)` and `(cafe_id, user_id, time)`) instead of an `id`.
- **Current busyness** = average of reports from the last 60 minutes (`BUSYNESS_WINDOW_MINUTES`). It is `null`
  ("No recent data") when there are none. The `max_busyness` filter **keeps** cafes with unknown busyness.
  A user can report once per cafe every 10 minutes. The detail page shows an hourly history built with
  `time_bucket()`.
- **Distance** uses the Haversine formula in plain SQL (`app/utils.py::haversine_km`), so PostGIS isn't needed.
- **Friendships** have a surrogate `id` (used by the accept/decline URLs) and a unique index on
  `(LEAST(a,b), GREATEST(a,b))`, so A→B and B→A can't both exist. Sending a request to someone who already
  requested you accepts it.
- **Check-in privacy rules** (`app/services/friends.py`): a check-in is visible only if the viewer is an
  **accepted** friend, the owner has `share_location = true`, and the check-in is **active** (not checked
  out, not expired). You can only check in with sharing on. Turning sharing off checks you out immediately.
  One active check-in per user: checking in somewhere else ends the previous one. Old check-ins stay as history.
- **Errors** are always `{"error": {"code", "message", "details?"}}` with proper HTTP status codes.
- **Auth**: JWT bearer token (12 h), stored in `localStorage` on the frontend (see TODO about cookies).

## API reference

All endpoints are prefixed with `/api`. 🔒 = requires `Authorization: Bearer <token>`.
List endpoints accept `?page=` (default 1) and `?per_page=` (default 20, max 100) and return
`{items, page, per_page, total, pages}`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET    | `/health` | | Health check (also pings DB) |
| POST   | `/auth/register` | | `{username, email, password}` → 201 `{access_token, user}` |
| POST   | `/auth/login` | | `{login (username or email), password}` → `{access_token, user}` |
| GET    | `/auth/me` | 🔒 | Current user |
| PATCH  | `/users/me/settings` | 🔒 | `{share_location: bool}`. Turning it off also checks you out |
| GET    | `/cafes` | | Search. Query: `lat, lng, max_distance_km, max_price (1-3), min_wifi (0-5), min_seats, max_busyness (1-5), q, sort=distance\|rating\|busyness\|name` |
| GET    | `/cafes/<id>` | optional | Detail: avg + attribute ratings, review count, current busyness, 12 h history, `friends_here` (if logged in). Optional `lat,lng` for distance |
| GET    | `/cafes/<id>/busyness` | | `{current, history}`; `?hours=24` (max 168) |
| POST   | `/cafes/<id>/busyness` | 🔒 | `{level: 1-5}` → 201. 429 if reported in last 10 min |
| GET    | `/cafes/<id>/reviews` | | Paginated, newest first. Optional `?user_id=` |
| POST   | `/cafes/<id>/reviews` | 🔒 | `{rating, space_rating?, quietness_rating?, wifi_rating?, cost_rating?, body?}` → 201. 409 if already reviewed |
| PUT    | `/reviews/<id>` | 🔒 owner | Partial update |
| DELETE | `/reviews/<id>` | 🔒 owner | 204 |
| GET    | `/friends` | 🔒 | Accepted friends |
| GET    | `/friends/requests` | 🔒 | Pending requests; `?direction=incoming` (default) or `outgoing` |
| POST   | `/friends/requests` | 🔒 | `{username}` → 201 (or 200 if it auto-accepted their request) |
| POST   | `/friends/requests/<id>/accept` | 🔒 recipient | Accept |
| DELETE | `/friends/requests/<id>` | 🔒 | Decline (recipient) or cancel (sender) |
| DELETE | `/friends/<user_id>` | 🔒 | Unfriend |
| GET    | `/friends/checkins` | 🔒 | Active check-ins of accepted friends who share |
| POST   | `/checkins` | 🔒 | `{cafe_id, duration_minutes? (15-480, default 180)}` → 201. 403 if sharing is off |
| POST   | `/checkins/checkout` | 🔒 | End your active check-in → `{checked_out: bool}` |
| GET    | `/checkins/me` | 🔒 | Your active check-in or `null` |

Status codes used: 200, 201, 204, 400 (bad params), 401 (no/invalid token), 403 (not allowed), 404,
409 (duplicate), 422 (validation), 429 (rate limit), 500.

## Where to extend (search for `TODO` in the code)

- **Backend:** user search endpoint, user-submitted cafes, "open now" filter, continuous aggregate and
  retention policy for busyness, refresh tokens/cookies, proximity check before check-in or reporting,
  check-in history/stats with `time_bucket()`, notifications for friend requests.
- **Frontend:** shareable filter URLs, profile pages, real-time updates (SSE/WebSockets instead of polling),
  PWA/offline support.

## Common commands

```bash
flask db migrate -m "describe change"   # after editing models.py, then review the generated file
flask db upgrade
flask db downgrade                      # undo last migration
npm run build                           # production build to frontend/dist
```
