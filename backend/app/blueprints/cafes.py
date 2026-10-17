"""Cafes: search/filter/sort, detail, busyness reports."""
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request
from sqlalchemy import exists, null, or_, select

from ..errors import APIError
from ..extensions import db
from ..models import BusynessReport, Cafe, utcnow
from ..schemas import BusynessReportSchema, CafeSearchSchema
from ..services.friends import visible_friend_checkins_stmt
from ..services.stats import (
    busyness_dict,
    busyness_history,
    current_busyness,
    current_busyness_subquery,
    rating_stats_subquery,
    to_float,
)
from ..utils import current_user_id, get_or_404, haversine_km, paginate

bp = Blueprint("cafes", __name__)


def cafe_query(lat: float | None = None, lng: float | None = None):
    """SELECT Cafe + distance + rating stats + current busyness. Returns (stmt, columns)."""
    rs = rating_stats_subquery()
    bz = current_busyness_subquery()
    distance = (
        haversine_km(Cafe.lat, Cafe.lng, lat, lng) if lat is not None else null()
    ).label("distance_km")
    stmt = (
        select(
            Cafe,
            distance,
            rs.c.avg_rating,
            rs.c.avg_space,
            rs.c.avg_quietness,
            rs.c.avg_wifi,
            rs.c.avg_cost,
            rs.c.review_count,
            bz.c.busyness,
            bz.c.busyness_reports,
        )
        .outerjoin(rs, rs.c.cafe_id == Cafe.id)
        .outerjoin(bz, bz.c.cafe_id == Cafe.id)
    )
    return stmt, distance, rs, bz


def serialize_cafe_row(row, detailed: bool = False) -> dict:
    cafe = row.Cafe
    data = cafe.to_dict()
    data["distance_km"] = to_float(row.distance_km, 2)
    data["avg_rating"] = to_float(row.avg_rating)
    data["review_count"] = int(row.review_count or 0)
    data["busyness"] = busyness_dict(row.busyness, row.busyness_reports)
    if detailed:
        data["attribute_ratings"] = {
            "space": to_float(row.avg_space),
            "quietness": to_float(row.avg_quietness),
            "wifi": to_float(row.avg_wifi),
            "cost": to_float(row.avg_cost),
        }
    return data


@bp.get("/cafes")
def list_cafes():
    """Search cafes.

    Query: lat, lng, max_distance_km, max_price, min_wifi, min_seats, max_busyness, q,
           sort=distance|rating|busyness|name, page, per_page
    Cafes with no recent busyness data are *included* when filtering by max_busyness.
    """
    args = CafeSearchSchema().load(request.args)
    lat, lng = args.get("lat"), args.get("lng")
    stmt, distance, rs, bz = cafe_query(lat, lng)

    if "max_distance_km" in args:
        stmt = stmt.where(distance <= args["max_distance_km"])
    if "max_price" in args:
        stmt = stmt.where(Cafe.price_level <= args["max_price"])
    if "min_wifi" in args:
        stmt = stmt.where(Cafe.wifi_quality >= args["min_wifi"])
        if args["min_wifi"] > 0:
            stmt = stmt.where(Cafe.has_wifi.is_(True))
    if "min_seats" in args:
        stmt = stmt.where(Cafe.seating_capacity >= args["min_seats"])
    if "max_busyness" in args:
        stmt = stmt.where(or_(bz.c.busyness.is_(None), bz.c.busyness <= args["max_busyness"]))
    if args.get("q"):
        like = f"%{args['q']}%"
        stmt = stmt.where(or_(Cafe.name.ilike(like), Cafe.address.ilike(like)))
    # TODO: "open now" filter using opening_hours.

    sort = args.get("sort") or ("distance" if lat is not None else "rating")
    order = {
        "distance": [distance.asc()],
        "rating": [rs.c.avg_rating.desc().nulls_last(), rs.c.review_count.desc().nulls_last()],
        "busyness": [bz.c.busyness.asc().nulls_last()],
        "name": [Cafe.name.asc()],
    }[sort]
    stmt = stmt.order_by(*order, Cafe.id)

    page = paginate(stmt, serialize_cafe_row)
    page["sort"] = sort
    return jsonify(page)


@bp.get("/cafes/<int:cafe_id>")
def get_cafe(cafe_id: int):
    """Cafe detail. Optional ?lat=&lng= adds distance. If logged in, includes friends here."""
    lat, lng = request.args.get("lat", type=float), request.args.get("lng", type=float)
    if (lat is None) != (lng is None):
        raise APIError(400, "bad_request", "lat and lng must be provided together")
    stmt, *_ = cafe_query(lat, lng)
    row = db.session.execute(stmt.where(Cafe.id == cafe_id)).first()
    if row is None:
        raise APIError(404, "not_found", "Cafe not found")

    data = serialize_cafe_row(row, detailed=True)
    data["busyness_history"] = busyness_history(cafe_id, hours=12)

    # Auth is optional here: logged-in users also see which friends are at this cafe.
    verify_jwt_in_request(optional=True)
    if get_jwt_identity():
        checkins = db.session.scalars(visible_friend_checkins_stmt(current_user_id(), cafe_id)).all()
        data["friends_here"] = [c.user.to_public_dict() for c in checkins]
    return jsonify(cafe=data)


@bp.get("/cafes/<int:cafe_id>/busyness")
def get_busyness(cafe_id: int):
    """Current busyness + hourly history (?hours=24, max 168)."""
    get_or_404(Cafe, cafe_id, "Cafe")
    hours = min(max(request.args.get("hours", 24, type=int), 1), 168)
    return jsonify(
        current=current_busyness(cafe_id),
        history=busyness_history(cafe_id, hours),
    )


@bp.post("/cafes/<int:cafe_id>/busyness")
@jwt_required()
def report_busyness(cafe_id: int):
    """Submit a 'how busy is it right now' report (1 = empty .. 5 = packed)."""
    get_or_404(Cafe, cafe_id, "Cafe")
    data = BusynessReportSchema().load(request.get_json(silent=True) or {})
    user_id = current_user_id()

    cooldown = current_app.config["BUSYNESS_REPORT_COOLDOWN_MINUTES"]
    recent = db.session.scalar(
        select(
            exists().where(
                BusynessReport.cafe_id == cafe_id,
                BusynessReport.user_id == user_id,
                BusynessReport.time > utcnow() - timedelta(minutes=cooldown),
            )
        )
    )
    if recent:
        raise APIError(429, "too_many_reports", f"You can report busyness for this cafe once every {cooldown} minutes")
    # TODO: only allow reports from users checked in nearby, to reduce spam.

    db.session.add(BusynessReport(cafe_id=cafe_id, user_id=user_id, level=data["level"], time=utcnow()))
    db.session.commit()

    return jsonify(busyness=current_busyness(cafe_id)), 201


# TODO: POST /cafes (user-submitted cafes, maybe admin-moderated) and PUT /cafes/<id>.
