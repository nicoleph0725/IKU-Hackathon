"""App configuration, read from environment variables (.env is loaded by python-dotenv)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def normalize_db_url(url: str | None) -> str | None:
    """Force the psycopg (v3) driver regardless of how the URL was written.

    Tiger Cloud / Heroku style URLs start with postgres:// or postgresql://, which
    SQLAlchemy would map to psycopg2. We use psycopg v3.
    """
    if not url:
        return url
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Cloud DBs drop idle connections; ping before use to avoid stale-connection errors.
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12")))
    # TODO: add refresh tokens if sessions need to last longer than a day.

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    # Domain settings
    BUSYNESS_WINDOW_MINUTES = 60          # reports newer than this count towards "current busyness"
    BUSYNESS_REPORT_COOLDOWN_MINUTES = 10  # one report per user per cafe per cooldown
    CHECKIN_DEFAULT_MINUTES = 180          # check-ins expire after 3 hours by default
    CHECKIN_MAX_MINUTES = 480
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = normalize_db_url(
        os.getenv("TEST_DATABASE_URL", "postgresql://studycafe:studycafe@localhost:5432/studycafe_test")
    )
    JWT_SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
