def test_register_logs_you_in(client):
    res = client.post("/api/auth/register", json={"username": "sam", "email": "Sam@Example.com", "password": "password123"})
    assert res.status_code == 201
    user = res.get_json()["user"]
    assert user["username"] == "sam"
    assert user["email"] == "sam@example.com"
    assert user["share_location"] is False  # opt-in: off by default
    assert "password_hash" not in user
    # the session cookie from registering is enough to call protected endpoints
    assert client.get("/api/auth/me").status_code == 200


def test_register_validation_errors(client):
    res = client.post("/api/auth/register", json={"username": "a!", "email": "nope", "password": "short"})
    assert res.status_code == 422
    assert set(res.get_json()["error"]["details"]) == {"username", "email", "password"}


def test_register_duplicate_username_case_insensitive(client, make_user):
    make_user("sam")
    res = client.post("/api/auth/register", json={"username": "SAM", "email": "other@example.com", "password": "password123"})
    assert res.status_code == 409


def test_login_with_username_or_email(client, make_user):
    make_user("sam")
    for login in ("sam", "SAM", "sam@example.com"):
        res = client.post("/api/auth/login", json={"login": login, "password": "password123"})
        assert res.status_code == 200, login


def test_login_wrong_password(client, make_user):
    make_user("sam")
    res = client.post("/api/auth/login", json={"login": "sam", "password": "wrong-password"})
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "invalid_credentials"


def test_me_requires_login(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "unauthorized"


def test_logout(make_user):
    sam = make_user("sam")
    assert sam.get("/api/auth/me").status_code == 200
    assert sam.post("/api/auth/logout").status_code == 204
    assert sam.get("/api/auth/me").status_code == 401


def test_unbuilt_endpoints_return_501(client):
    # Remove this test once the cafe endpoints are implemented.
    res = client.get("/api/cafes")
    assert res.status_code == 501
    assert res.get_json()["error"]["code"] == "not_implemented"
