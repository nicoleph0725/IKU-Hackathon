"""Test fixtures. Tests use a separate database (TEST_DATABASE_URL) that gets WIPED.

The schema is built by running the real Alembic migrations (including the hypertables).
"""
import itertools

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app import create_app
from app.config import TestConfig
from app.extensions import db

TABLES = "busyness_reports, checkins, reviews, friendships, cafes, users"


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.session.execute(text(f"DROP TABLE IF EXISTS {TABLES}, alembic_version CASCADE"))
        db.session.commit()
        upgrade()
        yield app
        db.session.remove()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    db.session.rollback()
    db.session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


_counter = itertools.count()


@pytest.fixture
def make_user(client):
    """Register a user via the API. Returns (user_id, auth_headers)."""

    def _make(username=None, password="password123"):
        username = username or f"user{next(_counter)}"
        res = client.post("/api/auth/register",
                          json={"username": username, "email": f"{username}@example.com", "password": password})
        assert res.status_code == 201, res.get_json()
        body = res.get_json()
        return body["user"]["id"], {"Authorization": f"Bearer {body['access_token']}"}

    return _make


# TODO: add tests per feature as you build it, e.g. tests/test_cafes.py (filters + distance),
#       tests/test_reviews.py, tests/test_friends.py (check-in visibility rules!).
