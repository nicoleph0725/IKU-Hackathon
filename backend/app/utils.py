"""Small shared helpers: pagination, current user, Haversine distance in SQL."""
from flask import current_app, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, literal, select

from .errors import APIError
from .extensions import db
from .models import User

EARTH_RADIUS_KM = 6371.0


def current_user_id() -> int:
    """User id from the JWT. Only call inside @jwt_required() views."""
    return int(get_jwt_identity())


def current_user() -> User:
    user = db.session.get(User, current_user_id())
    if user is None:  # token for a deleted user
        raise APIError(401, "unauthorized", "User no longer exists")
    return user


def get_or_404(model, ident, name: str | None = None):
    obj = db.session.get(model, ident)
    if obj is None:
        raise APIError(404, "not_found", f"{name or model.__name__} not found")
    return obj


def get_pagination() -> tuple[int, int]:
    """Read ?page=&per_page= with sane defaults and limits."""
    cfg = current_app.config
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = int(request.args.get("per_page", cfg["DEFAULT_PAGE_SIZE"]))
    except ValueError:
        raise APIError(400, "bad_request", "page and per_page must be integers")
    per_page = min(max(per_page, 1), cfg["MAX_PAGE_SIZE"])
    return page, per_page


def paginate(stmt, serialize, page: int | None = None, per_page: int | None = None) -> dict:
    """Run a SQLAlchemy select with LIMIT/OFFSET and return a standard page envelope.

    `serialize` turns one result row into a dict.
    """
    if page is None or per_page is None:
        page, per_page = get_pagination()
    total = db.session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.session.execute(stmt.limit(per_page).offset((page - 1) * per_page))
    # Single-entity selects come back as one-element rows; unwrap them for convenience.
    items = [serialize(r[0] if len(r) == 1 else r) for r in rows]
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page if total else 0,
    }


def haversine_km(lat_col, lng_col, lat: float, lng: float):
    """SQL expression for great-circle distance in km between a row's coords and a point.

    Pure SQL (no PostGIS). LEAST(1, ...) guards against floating point values slightly > 1.
    TODO: for thousands of cafes, add a bounding-box WHERE (lat/lng BETWEEN ...) first so an
    index on (lat, lng) can prune rows before this expression runs.
    """
    lat_p, lng_p = literal(lat), literal(lng)
    a = (
        func.power(func.sin(func.radians(lat_col - lat_p) / 2), 2)
        + func.cos(func.radians(lat_p))
        * func.cos(func.radians(lat_col))
        * func.power(func.sin(func.radians(lng_col - lng_p) / 2), 2)
    )
    return 2 * EARTH_RADIUS_KM * func.asin(func.sqrt(func.least(literal(1.0), a)))
