"""Shared helpers: 404 lookups, pagination.

For the logged-in user, use `from flask_login import current_user` in your views.
"""
from flask import current_app, request
from sqlalchemy import func, select

from .errors import APIError
from .extensions import db


def get_or_404(model, ident, name: str | None = None):
    obj = db.session.get(model, ident)
    if obj is None:
        raise APIError(404, "not_found", f"{name or model.__name__} not found")
    return obj


def paginate(stmt, serialize) -> dict:
    """Run a select with ?page=&per_page= and return {items, page, per_page, total, pages}.

    Example: return jsonify(paginate(select(Cafe).order_by(Cafe.name), lambda c: c.to_dict()))
    """
    cfg = current_app.config
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", cfg["DEFAULT_PAGE_SIZE"], type=int), 1), cfg["MAX_PAGE_SIZE"])
    total = db.session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.session.execute(stmt.limit(per_page).offset((page - 1) * per_page))
    items = [serialize(r[0] if len(r) == 1 else r) for r in rows]
    return {"items": items, "page": page, "per_page": per_page, "total": total,
            "pages": (total + per_page - 1) // per_page if total else 0}


# TODO: haversine_km(lat_col, lng_col, lat, lng) -> SQL expression for distance in km (no PostGIS).
#   d = 2 * 6371 * asin(sqrt(sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlng/2)))   (angles in radians)
#   Build it with sqlalchemy func.asin / func.sqrt / func.sin / func.cos / func.radians / func.power
#   so it can be used in .where(...) and .order_by(...) for GET /cafes.
