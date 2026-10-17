# ☕ StudySpot – find a study cafe

Hackathon starter: students search study cafes (space, busyness, distance, price, wifi), review them,
and see which cafe their friends are at (opt-in check-ins).

This is a **skeleton**. The plumbing works (app setup, database, migrations, login/register, routing, API
wrapper, map). The features are stubs marked with `TODO` comments. Unbuilt endpoints return
`501 Not Implemented`, and unbuilt pages show yellow TODO boxes. Search the code for `TODO` to see what's left.

**Stack:** Flask + SQLAlchemy + Alembic + Flask-Login (session cookies) · PostgreSQL/TimescaleDB (Tiger Cloud or Docker) ·
Vanilla JS + Tailwind + Vite + Leaflet

```
backend/
  app/
    __init__.py        app factory, registers blueprints
    config.py          settings from .env
    models.py          all tables (checkins + busyness_reports are TimescaleDB hypertables)
    schemas.py         input validation (marshmallow)
    errors.py          JSON errors + not_implemented()
    utils.py           current_user, get_or_404, paginate
    blueprints/        auth ✅ | users, cafes, reviews, friends, checkins (TODO)
  migrations/          database migrations (already creates every table)
  tests/               pytest (auth only so far)
frontend/src/
  main.js, router.js   routes -> views
  api.js               fetch wrapper (sends session cookie, handles errors)
  views/               login ✅ register ✅ | search, cafeDetail, writeReview, friends, settings (TODO)
  components/          navbar, map, toast, ui helpers
```

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv               # Windows: python -m venv .venv
source .venv/bin/activate           # macOS/Linux
.venv\Scripts\activate              # Windows
pip install -r requirements-dev.txt
cp .env.example .env                # Windows: copy .env.example .env
```

Activate the venv (`source .venv/bin/activate`) in every new terminal before running backend commands.

### 2. Database (pick one)

- **Tiger Cloud (no Docker needed):** create a service at <https://console.cloud.timescale.com>, copy its
  connection string, and set it in `backend/.env` as `DATABASE_URL=postgres://...?sslmode=require`.
  To share one database with the team, one person does step 3 and sends the string to the others privately.
- **Docker:** `docker compose up -d` from the repo root. The defaults in `.env.example` already match it.

### 3. Create the tables (once per database)

```bash
flask db upgrade
```

### 4. Run

```bash
flask run             # backend, in backend/  -> http://localhost:5000
npm install           # frontend, in frontend/ (first time only)
npm run dev           #                        -> http://localhost:5173
```

### Tests

```bash
pytest                # in backend/. Uses TEST_DATABASE_URL, which gets wiped. Never point it at the shared DB!
```

## API (prefix `/api`)

| Method | Path | Status |
|--------|------|--------|
| POST | `/auth/register` | ✅ |
| POST | `/auth/login` | ✅ |
| POST | `/auth/logout` | ✅ |
| GET | `/auth/me` | ✅ |
| PATCH | `/users/me/settings` | TODO |
| GET | `/cafes?lat=&lng=&max_distance_km=&max_price=&min_wifi=&min_seats=&max_busyness=&sort=` | TODO |
| GET | `/cafes/<id>` | TODO |
| POST | `/cafes/<id>/busyness` | TODO |
| GET / POST | `/cafes/<id>/reviews` | TODO |
| PUT / DELETE | `/reviews/<id>` | TODO |
| GET | `/friends` | TODO |
| GET / POST | `/friends/requests` | TODO |
| POST | `/friends/requests/<id>/accept` | TODO |
| DELETE | `/friends/<id>` | TODO |
| GET | `/friends/checkins` | TODO |
| POST | `/checkins`, `/checkins/checkout` | TODO |

Errors always look like `{"error": {"code": "...", "message": "..."}}`.

## Workflow tips

- **Changing a model:** edit `models.py`, then run `flask db migrate -m "what changed"` and `flask db upgrade`.
  Commit the new file in `migrations/versions/`.
- **Adding an endpoint:** write the route in the right blueprint, add a schema in `schemas.py` if it takes
  input, add a helper in `frontend/src/api.js`, and call it from a view.
- **Never commit `.env`** (it's git-ignored).
- **Mac users:** if every request returns 403, turn off System Settings → AirPlay Receiver (it uses port 5000).
