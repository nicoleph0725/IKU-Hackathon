"""Current user's settings."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..schemas import SettingsSchema
from ..services.checkins import checkout_active
from ..utils import current_user

bp = Blueprint("users", __name__)


@bp.patch("/users/me/settings")
@jwt_required()
def update_settings():
    data = SettingsSchema().load(request.get_json(silent=True) or {})
    user = current_user()
    user.share_location = data["share_location"]
    if not user.share_location:
        # Turning sharing off ends any active check-in immediately.
        checkout_active(user.id)
    db.session.commit()
    return jsonify(user=user.to_private_dict())


# TODO: GET /users/search?q= to find people to add as friends (currently exact username only).
# TODO: DELETE /users/me (account deletion; FKs cascade).
