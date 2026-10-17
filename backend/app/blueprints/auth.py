"""Auth with Flask-Login: register, login, logout, current user.

Logging in stores the user id in Flask's signed session cookie. The browser sends that cookie
automatically on every request, and @login_required / current_user read it.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_, select

from ..errors import APIError
from ..extensions import db
from ..models import User
from ..schemas import LoginSchema, RegisterSchema

bp = Blueprint("auth", __name__)


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
    login_user(user, remember=True)  # log them straight in
    return jsonify(user=user.to_private_dict()), 201


@bp.post("/auth/login")
def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    login_value = data["login"].strip().lower()
    user = db.session.scalars(
        select(User).where(or_(func.lower(User.username) == login_value, User.email == login_value))
    ).first()
    if user is None or not user.check_password(data["password"]):
        raise APIError(401, "invalid_credentials", "Incorrect username/email or password")
    login_user(user, remember=True)  # remember=True keeps them logged in after closing the browser
    return jsonify(user=user.to_private_dict())


@bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    return "", 204


@bp.get("/auth/me")
@login_required
def me():
    return jsonify(user=current_user.to_private_dict())
