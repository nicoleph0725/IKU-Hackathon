"""Friend requests and the check-in privacy rules."""
from datetime import datetime, timedelta

from sqlalchemy import update

from app.extensions import db
from app.models import CheckIn, utcnow


def visible(client, headers):
    return [(c["user"]["username"], c["cafe"]["id"]) for c in client.get("/api/friends/checkins", headers=headers).get_json()["items"]]


def username(client, headers):
    return client.get("/api/auth/me", headers=headers).get_json()["user"]["username"]


# --- Friend requests -------------------------------------------------------------

def test_friend_request_flow(client, make_user):
    a_id, a = make_user("anna")
    b_id, b = make_user("ben")

    res = client.post("/api/friends/requests", json={"username": "ben"}, headers=a)
    assert res.status_code == 201
    req_id = res.get_json()["friendship"]["id"]

    assert client.get("/api/friends/requests", headers=b).get_json()["total"] == 1
    assert client.get("/api/friends/requests", query_string={"direction": "outgoing"}, headers=a).get_json()["total"] == 1

    # Only the recipient can accept
    assert client.post(f"/api/friends/requests/{req_id}/accept", headers=a).status_code == 403
    assert client.post(f"/api/friends/requests/{req_id}/accept", headers=b).status_code == 200

    friends_of_a = client.get("/api/friends", headers=a).get_json()["items"]
    assert [f["user"]["username"] for f in friends_of_a] == ["ben"]
    assert [f["user"]["username"] for f in client.get("/api/friends", headers=b).get_json()["items"]] == ["anna"]

    # Duplicates in either direction are rejected
    assert client.post("/api/friends/requests", json={"username": "ben"}, headers=a).status_code == 409
    assert client.post("/api/friends/requests", json={"username": "anna"}, headers=b).status_code == 409

    # Unfriend
    assert client.delete(f"/api/friends/{b_id}", headers=a).status_code == 204
    assert client.get("/api/friends", headers=b).get_json()["total"] == 0
    assert client.delete(f"/api/friends/{b_id}", headers=a).status_code == 404


def test_friend_request_edge_cases(client, make_user):
    _, a = make_user("anna")
    _, b = make_user("ben")
    assert client.post("/api/friends/requests", json={"username": "anna"}, headers=a).status_code == 400
    assert client.post("/api/friends/requests", json={"username": "nobody"}, headers=a).status_code == 404

    # Reverse request auto-accepts
    client.post("/api/friends/requests", json={"username": "ben"}, headers=a)
    res = client.post("/api/friends/requests", json={"username": "anna"}, headers=b)
    assert res.status_code == 200
    assert res.get_json()["friendship"]["status"] == "accepted"


def test_decline_and_third_party_cannot_touch_request(client, make_user):
    _, a = make_user("anna")
    _, b = make_user("ben")
    _, c = make_user("cara")
    req_id = client.post("/api/friends/requests", json={"username": "ben"}, headers=a).get_json()["friendship"]["id"]
    assert client.post(f"/api/friends/requests/{req_id}/accept", headers=c).status_code == 404
    assert client.delete(f"/api/friends/requests/{req_id}", headers=c).status_code == 404
    assert client.delete(f"/api/friends/requests/{req_id}", headers=b).status_code == 204
    assert client.get("/api/friends/requests", headers=b).get_json()["total"] == 0


# --- Check-ins + visibility ------------------------------------------------------

def test_checkin_requires_opt_in(client, make_user, make_cafe):
    cafe_id = make_cafe()
    _, a = make_user()
    res = client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a)
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "sharing_disabled"


def test_accepted_friend_sees_checkin(client, make_user, make_cafe, befriend):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    assert client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1]).status_code == 201
    assert visible(client, b[1]) == [("anna", cafe_id)]
    # Cafe detail shows friends here to logged-in friends
    cafe = client.get(f"/api/cafes/{cafe_id}", headers=b[1]).get_json()["cafe"]
    assert [f["username"] for f in cafe["friends_here"]] == ["anna"]


def test_non_friends_and_pending_requests_cannot_see(client, make_user, make_cafe):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    stranger = make_user("sid")
    pending = make_user("pat")
    client.post("/api/friends/requests", json={"username": "pat"}, headers=a[1])  # never accepted
    client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1])
    assert visible(client, stranger[1]) == []
    assert visible(client, pending[1]) == []
    assert client.get(f"/api/cafes/{cafe_id}", headers=stranger[1]).get_json()["cafe"]["friends_here"] == []


def test_turning_off_sharing_hides_and_checks_out(client, make_user, make_cafe, befriend):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1])
    client.patch("/api/users/me/settings", json={"share_location": False}, headers=a[1])
    assert visible(client, b[1]) == []
    # Turning sharing back on does NOT resurrect the old check-in
    client.patch("/api/users/me/settings", json={"share_location": True}, headers=a[1])
    assert visible(client, b[1]) == []
    assert client.get("/api/checkins/me", headers=a[1]).get_json()["checkin"] is None


def test_checkout_hides_checkin(client, make_user, make_cafe, befriend):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1])
    res = client.post("/api/checkins/checkout", headers=a[1])
    assert res.get_json() == {"checked_out": True}
    assert visible(client, b[1]) == []
    assert client.post("/api/checkins/checkout", headers=a[1]).get_json() == {"checked_out": False}


def test_expired_checkin_is_hidden(client, app, make_user, make_cafe, befriend):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1])
    # Simulate time passing: move expiry into the past.
    db.session.execute(update(CheckIn).values(expires_at=utcnow() - timedelta(minutes=1)))
    db.session.commit()
    assert visible(client, b[1]) == []


def test_unfriending_hides_checkin(client, make_user, make_cafe, befriend):
    cafe_id = make_cafe()
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    client.post("/api/checkins", json={"cafe_id": cafe_id}, headers=a[1])
    client.delete(f"/api/friends/{a[0]}", headers=b[1])
    assert visible(client, b[1]) == []


def test_new_checkin_replaces_previous(client, make_user, make_cafe, befriend):
    first, second = make_cafe(name="One"), make_cafe(name="Two")
    a = make_user("anna", share_location=True)
    b = make_user("ben")
    befriend(a, b)
    client.post("/api/checkins", json={"cafe_id": first}, headers=a[1])
    res = client.post("/api/checkins", json={"cafe_id": second, "duration_minutes": 9999}, headers=a[1])
    assert res.status_code == 201
    assert visible(client, b[1]) == [("anna", second)]
    # duration is capped (480 min)
    checkin = res.get_json()["checkin"]
    span = datetime.fromisoformat(checkin["expires_at"]) - datetime.fromisoformat(checkin["checked_in_at"])
    assert span <= timedelta(minutes=480)
    # history is kept in the hypertable
    assert db.session.query(CheckIn).count() == 2
