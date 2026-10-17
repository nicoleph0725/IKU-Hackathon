REVIEW = {"rating": 4, "space_rating": 5, "quietness_rating": 3, "wifi_rating": 4, "cost_rating": 2, "body": "Nice"}


def test_create_and_list_reviews(client, make_user, make_cafe):
    cafe_id = make_cafe()
    _, headers = make_user("sam")
    res = client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=headers)
    assert res.status_code == 201
    review = res.get_json()["review"]
    assert review["user"]["username"] == "sam"
    assert review["space_rating"] == 5

    body = client.get(f"/api/cafes/{cafe_id}/reviews").get_json()
    assert body["total"] == 1 and body["items"][0]["body"] == "Nice"


def test_review_requires_auth_and_valid_ratings(client, make_user, make_cafe):
    cafe_id = make_cafe()
    _, headers = make_user()
    assert client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW).status_code == 401
    assert client.post(f"/api/cafes/{cafe_id}/reviews", json={**REVIEW, "rating": 6}, headers=headers).status_code == 422
    assert client.post(f"/api/cafes/{cafe_id}/reviews", json={"body": "no rating"}, headers=headers).status_code == 422
    assert client.post("/api/cafes/9999/reviews", json=REVIEW, headers=headers).status_code == 404


def test_one_review_per_user_per_cafe(client, make_user, make_cafe):
    cafe_id = make_cafe()
    _, headers = make_user()
    assert client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=headers).status_code == 201
    res = client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=headers)
    assert res.status_code == 409
    assert res.get_json()["error"]["code"] == "already_reviewed"


def test_cafe_averages_reflect_reviews(client, make_user, make_cafe):
    cafe_id = make_cafe()
    for rating in (5, 3):
        _, headers = make_user()
        client.post(f"/api/cafes/{cafe_id}/reviews", json={**REVIEW, "rating": rating, "wifi_rating": None}, headers=headers)
    cafe = client.get(f"/api/cafes/{cafe_id}").get_json()["cafe"]
    assert cafe["avg_rating"] == 4.0
    assert cafe["review_count"] == 2
    assert cafe["attribute_ratings"]["space"] == 5.0
    assert cafe["attribute_ratings"]["wifi"] is None


def test_only_owner_can_update_or_delete(client, make_user, make_cafe):
    cafe_id = make_cafe()
    _, owner = make_user()
    _, other = make_user()
    review_id = client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=owner).get_json()["review"]["id"]

    assert client.put(f"/api/reviews/{review_id}", json={"rating": 1}, headers=other).status_code == 403
    assert client.delete(f"/api/reviews/{review_id}", headers=other).status_code == 403

    res = client.put(f"/api/reviews/{review_id}", json={"rating": 2}, headers=owner)
    assert res.status_code == 200
    updated = res.get_json()["review"]
    assert updated["rating"] == 2
    assert updated["body"] == "Nice"  # partial update keeps other fields
    assert updated["updated_at"] is not None

    assert client.delete(f"/api/reviews/{review_id}", headers=owner).status_code == 204
    assert client.delete(f"/api/reviews/{review_id}", headers=owner).status_code == 404


def test_filter_reviews_by_user(client, make_user, make_cafe):
    cafe_id = make_cafe()
    a_id, a = make_user()
    _, b = make_user()
    client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=a)
    client.post(f"/api/cafes/{cafe_id}/reviews", json=REVIEW, headers=b)
    body = client.get(f"/api/cafes/{cafe_id}/reviews", query_string={"user_id": a_id}).get_json()
    assert body["total"] == 1 and body["items"][0]["user"]["id"] == a_id
