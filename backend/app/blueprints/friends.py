"""Friends: requests, accept, list, remove, and where friends are checked in."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..errors import not_implemented

bp = Blueprint("friends", __name__)


@bp.get("/friends")
@jwt_required()
def list_friends():
    # TODO: accepted friendships where the current user is requester OR addressee; return the other user.
    not_implemented("Friend list")


@bp.get("/friends/requests")
@jwt_required()
def list_requests():
    # TODO: pending requests sent TO the current user (and maybe ?direction=outgoing for sent ones).
    not_implemented("Friend requests")


@bp.post("/friends/requests")
@jwt_required()
def send_request():
    # TODO: {username} -> create Friendship(status="pending"). 404 unknown user, 400 yourself, 409 duplicate.
    not_implemented("Sending friend requests")


@bp.post("/friends/requests/<int:request_id>/accept")
@jwt_required()
def accept_request(request_id: int):
    # TODO: only the addressee can accept. Set status="accepted", accepted_at=utcnow().
    not_implemented("Accepting friend requests")


@bp.delete("/friends/<int:user_id>")
@jwt_required()
def remove_friend(user_id: int):
    # TODO: delete the accepted friendship between current user and user_id. Return 204.
    not_implemented("Removing friends")


@bp.get("/friends/checkins")
@jwt_required()
def friends_checkins():
    # TODO: active check-ins of friends. PRIVACY RULES - only include a check-in if ALL are true:
    #   1. the friendship is ACCEPTED (not pending)
    #   2. the friend has share_location = true
    #   3. the check-in is active: checked_out_at IS NULL AND expires_at > now()
    not_implemented("Friends' check-ins")
