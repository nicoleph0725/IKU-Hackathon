def test_register_returns_token_and_user(client):
    res = client.post("/api/auth/register", json={"username": "sam", "email": "Sam@Example.com", "password": "password123"})
    assert res.status_code == 201
    body = res.get_json()
    assert body["access_token"]
    assert body["user"]["username"] == "sam"
    assert body["user"]["email"] == "sam@example.com"
    assert body["user"]["share_location"] is False  # opt-in: off by default
    assert "password" not in body["user"] and "password_hash" not in body["user"]


def test_register_validation_errors(client):
    res = client.post("/api/auth/register", json={"username": "a!", "email": "nope", "password": "short"})
    assert res.status_code == 422
    err = res.get_json()["error"]
    assert err["code"] == "validation_error"
    assert set(err["details"]) == {"username", "email", "password"}


def test_register_duplicate_username_case_insensitive(client, make_user):
    make_user("sam")
    res = client.post("/api/auth/register", json={"username": "SAM", "email": "other@example.com", "password": "password123"})
    assert res.status_code == 409


def test_login_with_username_or_email(client, make_user):
    make_user("sam")
    for login in ("sam", "SAM", "sam@example.com"):
        res = client.post("/api/auth/login", json={"login": login, "password": "password123"})
        assert res.status_code == 200, login
        assert res.get_json()["access_token"]


def test_login_wrong_password(client, make_user):
    make_user("sam")
    res = client.post("/api/auth/login", json={"login": "sam", "password": "wrong-password"})
    assert res.status_code == 401
    assert res.get_json()["error"]["code"] == "invalid_credentials"


def test_me_requires_token(client, make_user):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    _, headers = make_user("sam")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["user"]["username"] == "sam"


def test_settings_toggle_share_location(client, make_user):
    _, headers = make_user()
    res = client.patch("/api/users/me/settings", json={"share_location": True}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["user"]["share_location"] is True
    assert client.patch("/api/users/me/settings", json={}, headers=headers).status_code == 422
