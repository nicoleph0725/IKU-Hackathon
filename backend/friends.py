"""Friend requests between users, stored in userconnections.

Each pair of users has at most one row, with userid1 < userid2. requestedby records
who sent a pending request (added with:
ALTER TABLE userconnections ADD COLUMN requestedby integer REFERENCES users(userid) ON DELETE CASCADE).
"""
from flask import Blueprint, jsonify, request, session

from db import get_conn

bp = Blueprint("friends", __name__, url_prefix="/api/friends")


def _pair(a, b):
    return (a, b) if a < b else (b, a)


@bp.before_request
def require_login():
    if not session.get("user_id"):
        return jsonify(error="Sign in to see your friends."), 401


@bp.get("")
def list_friends():
    """Accepted friends, requests sent to me, and requests I've sent."""
    me = session["user_id"]
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT u.userid, u.username, u.sharingat, c.status, c.requestedby
               FROM userconnections c
               JOIN users u ON u.userid = CASE WHEN c.userid1 = %s THEN c.userid2 ELSE c.userid1 END
               WHERE (c.userid1 = %s OR c.userid2 = %s) AND c.status IN ('pending', 'accepted')
               ORDER BY lower(u.username)""",
            (me, me, me),
        ).fetchall()

    result = {"friends": [], "incoming": [], "outgoing": []}
    for r in rows:
        user = {"id": r["userid"], "username": r["username"]}
        if r["status"] == "accepted":
            result["friends"].append({**user, "cafe": r["sharingat"]})
        elif r["requestedby"] == me:
            result["outgoing"].append(user)
        else:
            result["incoming"].append(user)
    return jsonify(result)


@bp.route("/location", methods=["GET", "PUT", "DELETE"])
def location():
    """The cafe I'm sharing that I'm at (users.sharingat). PUT {cafe} to share, DELETE to stop."""
    me = session["user_id"]
    cafe = None
    if request.method == "PUT":
        cafe = ((request.get_json(silent=True) or {}).get("cafe") or "").strip()[:200] or None
    with get_conn() as conn:
        if request.method != "GET":
            conn.execute("UPDATE users SET sharingat = %s WHERE userid = %s", (cafe, me))
        row = conn.execute("SELECT sharingat FROM users WHERE userid = %s", (me,)).fetchone()
    return jsonify(cafe=row["sharingat"] if row else None)


@bp.post("/request")
def send_request():
    me = session["user_id"]
    username = ((request.get_json(silent=True) or {}).get("username") or "").strip()
    if not username:
        return jsonify(error="Enter a username."), 400

    with get_conn() as conn:
        other = conn.execute(
            "SELECT userid, username FROM users WHERE lower(username) = lower(%s)", (username,)
        ).fetchone()
        if not other:
            return jsonify(error="No user with that username."), 404
        if other["userid"] == me:
            return jsonify(error="You can't add yourself."), 400

        a, b = _pair(me, other["userid"])
        existing = conn.execute(
            "SELECT status, requestedby FROM userconnections WHERE userid1 = %s AND userid2 = %s",
            (a, b),
        ).fetchone()

        if existing is None:
            conn.execute(
                """INSERT INTO userconnections (userid1, userid2, status, requestedby)
                   VALUES (%s, %s, 'pending', %s)""",
                (a, b, me),
            )
            return jsonify(ok=True, status="pending"), 201
        if existing["status"] == "accepted":
            return jsonify(error=f"You're already friends with {other['username']}."), 409
        if existing["status"] == "blocked":
            return jsonify(error="You can't add this user."), 403
        if existing["requestedby"] == me:
            return jsonify(error="Request already sent."), 409

        # They already asked us, so adding them back accepts it.
        conn.execute(
            "UPDATE userconnections SET status = 'accepted' WHERE userid1 = %s AND userid2 = %s",
            (a, b),
        )
        return jsonify(ok=True, status="accepted")


@bp.post("/<int:user_id>/accept")
def accept(user_id):
    a, b = _pair(session["user_id"], user_id)
    with get_conn() as conn:
        row = conn.execute(
            """UPDATE userconnections SET status = 'accepted'
               WHERE userid1 = %s AND userid2 = %s AND status = 'pending'
                 AND (requestedby IS NULL OR requestedby = %s)
               RETURNING connectionid""",
            (a, b, user_id),
        ).fetchone()
    if not row:
        return jsonify(error="That request no longer exists."), 404
    return jsonify(ok=True)


@bp.post("/<int:user_id>/decline")
def decline(user_id):
    """Decline a request sent to me, or cancel one I sent."""
    a, b = _pair(session["user_id"], user_id)
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM userconnections WHERE userid1 = %s AND userid2 = %s AND status = 'pending'",
            (a, b),
        )
    return jsonify(ok=True)
