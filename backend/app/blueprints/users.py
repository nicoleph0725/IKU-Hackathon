"""Current user's settings."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..errors import not_implemented

bp = Blueprint("users", __name__)


@bp.patch("/users/me/settings")
@jwt_required()
def update_settings():
    # TODO: validate {share_location: bool}, save it on current_user(), return {"user": user.to_private_dict()}
    # TODO: when share_location is turned OFF, also end the user's active check-in (privacy).
    not_implemented("Updating settings")
