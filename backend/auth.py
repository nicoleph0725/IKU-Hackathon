from flask import Blueprint, jsonify, request, session
from psycopg.errors import UniqueViolation
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_conn

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _public(user):
    return {"id": user["userid"], "email": user["email"], "username": user["username"]}


@bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if "@" not in email or len(email) > 254:
        return jsonify(error="Enter a valid email address."), 400
    if not username or len(username) > 40:
        return jsonify(error="Enter a username (max 40 characters)."), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400

    try:
        with get_conn() as conn:
            user = conn.execute(
                """INSERT INTO users (email, username, password)
                   VALUES (%s, %s, %s)
                   RETURNING userid, email, username""",
                (email, username, generate_password_hash(password)),
            ).fetchone()
    except UniqueViolation as e:
        if "username" in (e.diag.constraint_name or ""):
            return jsonify(error="That username is taken."), 409
        return jsonify(error="An account with that email already exists."), 409

    session.clear()
    session["user_id"] = user["userid"]
    return jsonify(user=_public(user)), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    with get_conn() as conn:
        user = conn.execute(
            "SELECT userid, email, username, password FROM users WHERE email = %s",
            (email,),
        ).fetchone()

    if not user or not check_password_hash(user["password"], password):
        return jsonify(error="Incorrect email or password."), 401

    session.clear()
    session["user_id"] = user["userid"]
    return jsonify(user=_public(user))


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@bp.get("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(user=None)
    with get_conn() as conn:
        user = conn.execute(
            "SELECT userid, email, username FROM users WHERE userid = %s", (user_id,)
        ).fetchone()
    return jsonify(user=_public(user) if user else None)