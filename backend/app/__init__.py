"""Study Cafe Finder API - application factory."""
import logging

from flask import Flask, jsonify
from sqlalchemy import text

from .config import Config
from .errors import register_error_handlers
from .extensions import cors, db, jwt, migrate


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.sort_keys = False  # keep keys in the order we build them
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL is not set. Copy backend/.env.example to backend/.env.")

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from . import models  # noqa: F401  (register models with SQLAlchemy / Alembic)
    from .blueprints import auth, cafes, checkins, friends, reviews, users

    for bp in (auth.bp, users.bp, cafes.bp, reviews.bp, friends.bp, checkins.bp):
        app.register_blueprint(bp, url_prefix="/api")

    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok")

    return app
