"""Cafes: search/filter, detail, busyness reports."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..errors import not_implemented

bp = Blueprint("cafes", __name__)


@bp.get("/cafes")
def list_cafes():
    # TODO: search cafes. Query params:
    #   lat, lng, max_distance_km  -> distance via Haversine in SQL (see TODO in utils.py)
    #   max_price, min_wifi, min_seats  -> simple WHERE filters on Cafe columns
    #   max_busyness  -> average BusynessReport.level over the last 60 min, per cafe (subquery + outer join)
    #   sort=distance|rating|busyness
    # Return paginate(stmt, serializer) from utils.py.
    not_implemented("Cafe search")


@bp.get("/cafes/<int:cafe_id>")
def get_cafe(cafe_id: int):
    # TODO: return the cafe + average ratings (overall and per attribute), review count,
    #       current busyness. 404 if not found (utils.get_or_404).
    # IDEA: hourly busyness history with TimescaleDB: func.time_bucket(timedelta(hours=1), BusynessReport.time)
    not_implemented("Cafe detail")


@bp.post("/cafes/<int:cafe_id>/busyness")
@jwt_required()
def report_busyness(cafe_id: int):
    # TODO: validate {level: 1-5}, insert a BusynessReport(time=utcnow(), cafe_id, user_id, level), return 201.
    # IDEA: rate-limit to one report per user per cafe every ~10 minutes (return 429).
    not_implemented("Busyness reports")
