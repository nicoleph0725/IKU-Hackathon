"""Check-ins: opt-in, cafe-level presence (no live GPS) that expires after a few hours."""
from flask import Blueprint
from flask_login import login_required

from ..errors import not_implemented

bp = Blueprint("checkins", __name__)


@bp.post("/checkins")
@login_required
def check_in():
    # TODO: {cafe_id, duration_minutes?}
    #   - 403 if the user's share_location is false (sharing is opt-in)
    #   - end any existing active check-in first (one at a time)
    #   - insert CheckIn(time=utcnow(), user_id, cafe_id, expires_at=now + ~3 hours), return 201
    not_implemented("Check-in")


@bp.post("/checkins/checkout")
@login_required
def check_out():
    # TODO: set checked_out_at=utcnow() on the user's active check-in.
    not_implemented("Check-out")
