"""App configuration, read from environment variables (.env is loaded by python-dotenv)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def normalize_db_url(url: str | None) -> str | None:
    """Force the psycopg (v3) driver. Tiger Cloud URLs start with postgres:// or postgresql://."""
    if not url:
        return url
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Config:
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # cloud DBs drop idle connections
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12")))

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    # TODO: add feature settings here, e.g. BUSYNESS_WINDOW_MINUTES = 60, CHECKIN_DEFAULT_MINUTES = 180


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = normalize_db_url(
        os.getenv("TEST_DATABASE_URL", "postgresql://studycafe:studycafe@localhost:5432/studycafe_test")
    )
    JWT_SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
