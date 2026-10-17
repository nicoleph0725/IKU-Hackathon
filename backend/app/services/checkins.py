"""Check-in rules shared by several blueprints.

A check-in is "active" while checked_out_at IS NULL and expires_at > now().
Expired rows are kept as history in the hypertable.
"""
from sqlalchemy import select, update

from ..extensions import db
from ..models import CheckIn, utcnow


def active_checkin_filter():
    return (CheckIn.checked_out_at.is_(None), CheckIn.expires_at > utcnow())


def get_active_checkin(user_id: int) -> CheckIn | None:
    return db.session.scalars(
        select(CheckIn).where(CheckIn.user_id == user_id, *active_checkin_filter()).order_by(CheckIn.time.desc())
    ).first()


def checkout_active(user_id: int) -> int:
    """End any active check-in for the user. Returns number of rows closed. Caller commits."""
    result = db.session.execute(
        update(CheckIn)
        .where(CheckIn.user_id == user_id, *active_checkin_filter())
        .values(checked_out_at=utcnow())
    )
    return result.rowcount
