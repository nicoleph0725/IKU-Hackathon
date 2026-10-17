"""Aggregate queries over reviews and busyness reports, reused by list + detail endpoints."""
from datetime import timedelta

from flask import current_app
from sqlalchemy import func, select

from ..extensions import db
from ..models import BusynessReport, Review, utcnow

BUSYNESS_LABELS = {1: "Empty", 2: "Quiet", 3: "Moderate", 4: "Busy", 5: "Packed"}


def to_float(value, ndigits=1):
    return round(float(value), ndigits) if value is not None else None


def busyness_label(level) -> str | None:
    return BUSYNESS_LABELS[int(round(float(level)))] if level is not None else None


def busyness_dict(level, report_count) -> dict:
    return {
        "level": to_float(level),
        "label": busyness_label(level) or "No recent data",
        "report_count": int(report_count or 0),
        "window_minutes": current_app.config["BUSYNESS_WINDOW_MINUTES"],
    }


def rating_stats_subquery():
    """Per-cafe review averages."""
    return (
        select(
            Review.cafe_id.label("cafe_id"),
            func.avg(Review.rating).label("avg_rating"),
            func.avg(Review.space_rating).label("avg_space"),
            func.avg(Review.quietness_rating).label("avg_quietness"),
            func.avg(Review.wifi_rating).label("avg_wifi"),
            func.avg(Review.cost_rating).label("avg_cost"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.cafe_id)
        .subquery("rating_stats")
    )


def current_busyness_subquery():
    """Per-cafe average busyness level over the recent window (default: last 60 minutes).

    TODO: weight newer reports more heavily (e.g. exponential decay), or replace with a
    TimescaleDB continuous aggregate if report volume gets large.
    """
    since = utcnow() - timedelta(minutes=current_app.config["BUSYNESS_WINDOW_MINUTES"])
    return (
        select(
            BusynessReport.cafe_id.label("cafe_id"),
            func.avg(BusynessReport.level).label("busyness"),
            func.count().label("busyness_reports"),
        )
        .where(BusynessReport.time >= since)
        .group_by(BusynessReport.cafe_id)
        .subquery("current_busyness")
    )


def current_busyness(cafe_id: int) -> dict:
    bz = current_busyness_subquery()
    row = db.session.execute(select(bz.c.busyness, bz.c.busyness_reports).where(bz.c.cafe_id == cafe_id)).first()
    return busyness_dict(row.busyness if row else None, row.busyness_reports if row else 0)


def busyness_history(cafe_id: int, hours: int = 24) -> list[dict]:
    """Hourly average busyness using TimescaleDB's time_bucket()."""
    since = utcnow() - timedelta(hours=hours)
    bucket = func.time_bucket(timedelta(hours=1), BusynessReport.time).label("bucket")
    rows = db.session.execute(
        select(bucket, func.avg(BusynessReport.level), func.count())
        .where(BusynessReport.cafe_id == cafe_id, BusynessReport.time >= since)
        .group_by(bucket)
        .order_by(bucket)
    )
    return [{"hour": b.isoformat(), "level": to_float(avg), "report_count": n} for b, avg, n in rows]
