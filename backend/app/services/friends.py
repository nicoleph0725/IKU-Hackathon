"""Friendship queries and the check-in visibility rule.

Visibility rule (privacy): user A can see user B's check-in only if
  1. A and B have an *accepted* friendship (either direction),
  2. B has share_location = true (opt-in, can be switched off at any time),
  3. the check-in is active (not checked out, not expired).
"""
from sqlalchemy import and_, case, or_, select

from ..models import CheckIn, Friendship, User
from .checkins import active_checkin_filter


def friendship_between(a: int, b: int):
    """WHERE clause matching the friendship row between two users, in either direction."""
    return or_(
        and_(Friendship.requester_id == a, Friendship.addressee_id == b),
        and_(Friendship.requester_id == b, Friendship.addressee_id == a),
    )


def friend_ids_select(user_id: int):
    """SELECT of the ids of all accepted friends of user_id."""
    other = case((Friendship.requester_id == user_id, Friendship.addressee_id), else_=Friendship.requester_id)
    return select(other).where(
        Friendship.status == "accepted",
        or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
    )


def visible_friend_checkins_stmt(viewer_id: int, cafe_id: int | None = None):
    stmt = (
        select(CheckIn)
        .join(User, User.id == CheckIn.user_id)
        .where(
            CheckIn.user_id.in_(friend_ids_select(viewer_id)),
            User.share_location.is_(True),
            *active_checkin_filter(),
        )
        .order_by(CheckIn.time.desc())
    )
    if cafe_id is not None:
        stmt = stmt.where(CheckIn.cafe_id == cafe_id)
    return stmt
