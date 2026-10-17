"""Current user's settings."""
from flask import Blueprint
from flask_login import login_required

from ..errors import not_implemented

bp = Blueprint("users", __name__)


@bp.patch("/users/me/settings")
@login_required
def update_settings():
    # TODO: validate {share_location: bool}, save it on current_user (from flask_login), return {"user": user.to_private_dict()}
    # TODO: when share_location is turned OFF, also end the user's active check-in (privacy).
    not_implemented("Updating settings")
