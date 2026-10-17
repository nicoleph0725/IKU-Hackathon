"""Auth: register, login, current user."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import func, or_, select

from ..errors import APIError
from ..extensions import db
from ..models import User
from ..schemas import LoginSchema, RegisterSchema
from ..utils import current_user

bp = Blueprint("auth", __name__)


def token_response(user: User, status: int = 200):
    # JWT "sub" must be a string (Flask-JWT-Extended >= 4.6).
    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token, user=user.to_private_dict()), status


@bp.post("/auth/register")
def register():
    data = RegisterSchema().load(request.get_json(silent=True) or {})
    username, email = data["username"], data["email"].lower()

    existing = db.session.scalars(
        select(User).where(or_(func.lower(User.username) == username.lower(), User.email == email))
    ).first()
    if existing:
        field = "email" if existing.email == email else "username"
        raise APIError(409, "conflict", f"That {field} is already taken", {field: ["Already taken"]})

    user = User(username=username, email=email)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return token_response(user, 201)


@bp.post("/auth/login")
def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    login_value = data["login"].strip().lower()
    user = db.session.scalars(
        select(User).where(or_(func.lower(User.username) == login_value, User.email == login_value))
    ).first()
    if user is None or not user.check_password(data["password"]):
        raise APIError(401, "invalid_credentials", "Incorrect username/email or password")
    return token_response(user)


@bp.get("/auth/me")
@jwt_required()
def me():
    return jsonify(user=current_user().to_private_dict())
