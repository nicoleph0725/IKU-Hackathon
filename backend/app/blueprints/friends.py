"""Friends: requests, accept/decline, list, remove, and where friends are checked in."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_, select

from ..errors import APIError
from ..extensions import db
from ..models import Friendship, User, iso, utcnow
from ..schemas import FriendRequestSchema
from ..services.friends import friendship_between, visible_friend_checkins_stmt
from ..utils import current_user_id, paginate

bp = Blueprint("friends", __name__)


def friend_dict(f: Friendship, me: int) -> dict:
    return {"friendship_id": f.id, "user": f.other(me).to_public_dict(), "since": iso(f.accepted_at)}


def request_dict(f: Friendship) -> dict:
    return {
        "id": f.id,
        "requester": f.requester.to_public_dict(),
        "addressee": f.addressee.to_public_dict(),
        "status": f.status,
        "created_at": iso(f.created_at),
    }


@bp.get("/friends")
@jwt_required()
def list_friends():
    me = current_user_id()
    stmt = (
        select(Friendship)
        .where(Friendship.status == "accepted", or_(Friendship.requester_id == me, Friendship.addressee_id == me))
        .order_by(Friendship.accepted_at.desc())
    )
    return jsonify(paginate(stmt, lambda f: friend_dict(f, me)))


@bp.get("/friends/requests")
@jwt_required()
def list_requests():
    """Pending requests. ?direction=incoming (default) | outgoing"""
    me = current_user_id()
    direction = request.args.get("direction", "incoming")
    if direction not in ("incoming", "outgoing"):
        raise APIError(400, "bad_request", "direction must be 'incoming' or 'outgoing'")
    col = Friendship.addressee_id if direction == "incoming" else Friendship.requester_id
    stmt = select(Friendship).where(Friendship.status == "pending", col == me).order_by(Friendship.created_at.desc())
    page = paginate(stmt, request_dict)
    page["direction"] = direction
    return jsonify(page)


@bp.post("/friends/requests")
@jwt_required()
def send_request():
    """Send a friend request by username. If they already asked you, this accepts it."""
    me = current_user_id()
    data = FriendRequestSchema().load(request.get_json(silent=True) or {})
    target = db.session.scalars(select(User).where(func.lower(User.username) == data["username"].lower())).first()
    if target is None:
        raise APIError(404, "not_found", "No user with that username")
    if target.id == me:
        raise APIError(400, "bad_request", "You cannot add yourself")

    existing = db.session.scalars(select(Friendship).where(friendship_between(me, target.id))).first()
    if existing:
        if existing.status == "accepted":
            raise APIError(409, "already_friends", "You are already friends")
        if existing.requester_id == me:
            raise APIError(409, "already_requested", "Friend request already sent")
        # They had already sent us a request -> accept it.
        existing.status, existing.accepted_at = "accepted", utcnow()
        db.session.commit()
        return jsonify(friendship=request_dict(existing)), 200

    friendship = Friendship(requester_id=me, addressee_id=target.id, status="pending")
    db.session.add(friendship)
    db.session.commit()
    # TODO: notify the addressee (email / push / in-app notification).
    return jsonify(friendship=request_dict(friendship)), 201


def get_pending_request(request_id: int) -> Friendship:
    f = db.session.get(Friendship, request_id)
    me = current_user_id()
    # 404 (not 403) for requests that don't involve you, so ids can't be probed.
    if f is None or f.status != "pending" or me not in (f.requester_id, f.addressee_id):
        raise APIError(404, "not_found", "Friend request not found")
    return f


@bp.post("/friends/requests/<int:request_id>/accept")
@jwt_required()
def accept_request(request_id: int):
    f = get_pending_request(request_id)
    if f.addressee_id != current_user_id():
        raise APIError(403, "forbidden", "Only the recipient can accept a friend request")
    f.status, f.accepted_at = "accepted", utcnow()
    db.session.commit()
    return jsonify(friendship=request_dict(f))


@bp.delete("/friends/requests/<int:request_id>")
@jwt_required()
def decline_request(request_id: int):
    """Decline (recipient) or cancel (sender) a pending request."""
    f = get_pending_request(request_id)
    db.session.delete(f)
    db.session.commit()
    return "", 204


@bp.delete("/friends/<int:user_id>")
@jwt_required()
def remove_friend(user_id: int):
    """Unfriend. <user_id> is the friend's user id."""
    me = current_user_id()
    f = db.session.scalars(
        select(Friendship).where(friendship_between(me, user_id), Friendship.status == "accepted")
    ).first()
    if f is None:
        raise APIError(404, "not_found", "You are not friends with this user")
    db.session.delete(f)
    db.session.commit()
    return "", 204


@bp.get("/friends/checkins")
@jwt_required()
def friends_checkins():
    """Active check-ins of accepted friends who have opted in to sharing."""
    return jsonify(paginate(visible_friend_checkins_stmt(current_user_id()), lambda c: c.to_dict()))
