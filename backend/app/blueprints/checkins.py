"""Check-ins: opt-in, cafe-level presence (no live GPS). Expire automatically."""
from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from ..errors import APIError
from ..extensions import db
from ..models import Cafe, CheckIn, utcnow
from ..schemas import CheckInSchema
from ..services.checkins import checkout_active, get_active_checkin
from ..utils import current_user, current_user_id, get_or_404

bp = Blueprint("checkins", __name__)


@bp.post("/checkins")
@jwt_required()
def check_in():
    user = current_user()
    if not user.share_location:
        raise APIError(
            403, "sharing_disabled", "Turn on location sharing in settings before checking in"
        )
    data = CheckInSchema().load(request.get_json(silent=True) or {})
    get_or_404(Cafe, data["cafe_id"], "Cafe")

    cfg = current_app.config
    minutes = min(data.get("duration_minutes", cfg["CHECKIN_DEFAULT_MINUTES"]), cfg["CHECKIN_MAX_MINUTES"])

    # One active check-in per user: checking in elsewhere ends the previous one.
    checkout_active(user.id)
    now = utcnow()
    checkin = CheckIn(time=now, user_id=user.id, cafe_id=data["cafe_id"], expires_at=now + timedelta(minutes=minutes))
    db.session.add(checkin)
    db.session.commit()
    # TODO: optionally verify the user is physically near the cafe (browser geolocation).
    return jsonify(checkin=checkin.to_dict()), 201


@bp.post("/checkins/checkout")
@jwt_required()
def check_out():
    """End the active check-in. Idempotent: returns checked_out=false if there was none."""
    closed = checkout_active(current_user_id())
    db.session.commit()
    return jsonify(checked_out=closed > 0)


@bp.get("/checkins/me")
@jwt_required()
def my_checkin():
    checkin = get_active_checkin(current_user_id())
    return jsonify(checkin=checkin.to_dict() if checkin else None)


# TODO: GET /checkins/history - the user's own past check-ins (study streaks, stats)
#       using time_bucket() over the checkins hypertable.
