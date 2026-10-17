from datetime import timedelta

import pytest

from app.extensions import db
from app.models import BusynessReport, utcnow

# Reference point: Trafalgar Square. Known distances (great-circle):
#   British Museum (51.5194, -0.1270)  ~1.27 km
#   Tower of London (51.5081, -0.0759) ~3.55 km
#   Brixton (51.4626, -0.1123)         ~5.13 km
ORIGIN = {"lat": 51.5080, "lng": -0.1281}


@pytest.fixture
def cafes(make_cafe):
    return {
        "museum": make_cafe(name="Museum Cafe", lat=51.5194, lng=-0.1270, price_level=1, seating_capacity=20, wifi_quality=5),
        "tower": make_cafe(name="Tower Cafe", lat=51.5081, lng=-0.0759, price_level=3, seating_capacity=100, wifi_quality=2),
        "brixton": make_cafe(name="Brixton Cafe", lat=51.4626, lng=-0.1123, price_level=2, seating_capacity=60,
                             has_wifi=False, wifi_quality=0),
    }


def names(res):
    return [c["name"] for c in res.get_json()["items"]]


def add_report(cafe_id, user_id, level, minutes_ago):
    db.session.add(BusynessReport(time=utcnow() - timedelta(minutes=minutes_ago), cafe_id=cafe_id,
                                  user_id=user_id, level=level))
    db.session.commit()


def test_distance_is_computed_and_sorted(client, cafes):
    res = client.get("/api/cafes", query_string={**ORIGIN, "sort": "distance"})
    assert res.status_code == 200
    items = res.get_json()["items"]
    assert [c["name"] for c in items] == ["Museum Cafe", "Tower Cafe", "Brixton Cafe"]
    assert items[0]["distance_km"] == pytest.approx(1.27, abs=0.1)
    assert items[1]["distance_km"] == pytest.approx(3.55, abs=0.1)
    assert items[2]["distance_km"] == pytest.approx(5.13, abs=0.1)


def test_max_distance_filter(client, cafes):
    res = client.get("/api/cafes", query_string={**ORIGIN, "max_distance_km": 4})
    assert names(res) == ["Museum Cafe", "Tower Cafe"]


def test_price_wifi_seats_filters(client, cafes):
    assert names(client.get("/api/cafes", query_string={"max_price": 2, "sort": "name"})) == ["Brixton Cafe", "Museum Cafe"]
    assert names(client.get("/api/cafes", query_string={"min_wifi": 1, "sort": "name"})) == ["Museum Cafe", "Tower Cafe"]
    assert names(client.get("/api/cafes", query_string={"min_wifi": 4})) == ["Museum Cafe"]
    assert names(client.get("/api/cafes", query_string={"min_seats": 50, "sort": "name"})) == ["Brixton Cafe", "Tower Cafe"]


def test_busyness_uses_only_recent_reports(client, cafes, make_user):
    uid, _ = make_user()
    add_report(cafes["museum"], uid, 5, minutes_ago=10)
    add_report(cafes["museum"], uid, 3, minutes_ago=20)
    add_report(cafes["tower"], uid, 1, minutes_ago=5)
    add_report(cafes["tower"], uid, 5, minutes_ago=180)  # too old: ignored

    items = {c["name"]: c for c in client.get("/api/cafes").get_json()["items"]}
    assert items["Museum Cafe"]["busyness"]["level"] == 4.0
    assert items["Tower Cafe"]["busyness"]["level"] == 1.0
    assert items["Brixton Cafe"]["busyness"]["level"] is None

    # max_busyness keeps cafes with unknown busyness
    res = client.get("/api/cafes", query_string={"max_busyness": 2, "sort": "name"})
    assert names(res) == ["Brixton Cafe", "Tower Cafe"]
    # sort=busyness: least busy first, unknown last
    assert names(client.get("/api/cafes", query_string={"sort": "busyness"})) == ["Tower Cafe", "Museum Cafe", "Brixton Cafe"]


def test_invalid_search_params(client, cafes):
    assert client.get("/api/cafes", query_string={"lat": 51.5}).status_code == 422
    assert client.get("/api/cafes", query_string={"sort": "distance"}).status_code == 422
    assert client.get("/api/cafes", query_string={"max_price": 9}).status_code == 422


def test_pagination(client, make_cafe):
    for i in range(5):
        make_cafe(name=f"Cafe {i}")
    body = client.get("/api/cafes", query_string={"per_page": 2, "page": 3, "sort": "name"}).get_json()
    assert body["total"] == 5 and body["pages"] == 3 and body["page"] == 3
    assert [c["name"] for c in body["items"]] == ["Cafe 4"]


def test_cafe_detail_and_404(client, cafes):
    res = client.get(f"/api/cafes/{cafes['museum']}")
    assert res.status_code == 200
    cafe = res.get_json()["cafe"]
    assert cafe["review_count"] == 0
    assert set(cafe["attribute_ratings"]) == {"space", "quietness", "wifi", "cost"}
    assert "busyness" in cafe and "busyness_history" in cafe
    assert "friends_here" not in cafe  # anonymous
    res = client.get("/api/cafes/99999")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "not_found"


def test_report_busyness_with_cooldown(client, cafes, make_user):
    _, headers = make_user()
    url = f"/api/cafes/{cafes['museum']}/busyness"
    assert client.post(url, json={"level": 3}).status_code == 401
    assert client.post(url, json={"level": 7}, headers=headers).status_code == 422
    res = client.post(url, json={"level": 3}, headers=headers)
    assert res.status_code == 201
    assert res.get_json()["busyness"]["level"] == 3.0
    assert client.post(url, json={"level": 4}, headers=headers).status_code == 429


def test_busyness_history_uses_time_buckets(client, cafes, make_user):
    uid, _ = make_user()
    add_report(cafes["museum"], uid, 2, minutes_ago=5)
    add_report(cafes["museum"], uid, 4, minutes_ago=6)
    add_report(cafes["museum"], uid, 5, minutes_ago=200)
    history = client.get(f"/api/cafes/{cafes['museum']}/busyness").get_json()["history"]
    assert sum(h["report_count"] for h in history) == 3
    assert 2 <= len(history) <= 3  # hourly buckets
