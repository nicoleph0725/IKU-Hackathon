"""Test fixtures.

Tests run against a real PostgreSQL + TimescaleDB database (TEST_DATABASE_URL, default
studycafe_test from docker-compose) because hypertables, time_bucket() and now() logic
can't be faked with SQLite. The schema is built by running the real Alembic migrations,
so the migration (including hypertable creation) is tested too.
"""
import itertools

import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Cafe

TABLES = "busyness_reports, checkins, reviews, friendships, cafes, users"


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        # Start from an empty schema every run, then apply migrations.
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

    def _make(username=None, share_location=False, password="password123"):
        username = username or f"user{next(_counter)}"
        res = client.post(
            "/api/auth/register",
            json={"username": username, "email": f"{username}@example.com", "password": password},
        )
        assert res.status_code == 201, res.get_json()
        body = res.get_json()
        headers = {"Authorization": f"Bearer {body['access_token']}"}
        if share_location:
            assert client.patch("/api/users/me/settings", json={"share_location": True}, headers=headers).status_code == 200
        return body["user"]["id"], headers

    return _make


@pytest.fixture
def make_cafe(app):
    def _make(**overrides):
        data = dict(
            name="Test Cafe", address="1 Test St", lat=51.5074, lng=-0.1278,
            price_level=2, seating_capacity=40, has_wifi=True, wifi_quality=3,
        )
        data.update(overrides)
        cafe = Cafe(**data)
        db.session.add(cafe)
        db.session.commit()
        return cafe.id

    return _make


@pytest.fixture
def befriend(client):
    """Make two users accepted friends."""

    def _befriend(a, b):
        (a_id, a_headers), (b_id, b_headers) = a, b
        username_b = client.get("/api/auth/me", headers=b_headers).get_json()["user"]["username"]
        req = client.post("/api/friends/requests", json={"username": username_b}, headers=a_headers).get_json()
        res = client.post(f"/api/friends/requests/{req['friendship']['id']}/accept", headers=b_headers)
        assert res.status_code == 200

    return _befriend
