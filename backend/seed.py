"""Minimal demo data. Run from backend/ (venv active, after `flask db upgrade`):  python seed.py

WARNING: wipes all existing rows first.
Demo logins: alice / password123, bob / password123
"""
from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import Cafe, User

CAFES = [
    # name, address, lat, lng, price_level, seats, has_wifi, wifi_quality
    ("The Reading Room", "12 Gower St, London WC1E", 51.5222, -0.1316, 2, 60, True, 5),
    ("Camden Cuppa", "102 Camden High St, London NW1", 51.5390, -0.1426, 1, 40, True, 3),
    ("Southbank Steam", "9 Belvedere Rd, London SE1", 51.5055, -0.1160, 3, 80, False, 0),
]
# TODO: add more cafes, plus sample reviews / busyness reports / friendships once those features exist.


def seed():
    app = create_app()
    with app.app_context():
        db.session.execute(text(
            "TRUNCATE busyness_reports, checkins, reviews, friendships, cafes, users RESTART IDENTITY CASCADE"
        ))
        db.session.add_all(
            Cafe(name=n, address=a, lat=lat, lng=lng, price_level=p, seating_capacity=s, has_wifi=w, wifi_quality=q)
            for n, a, lat, lng, p, s, w, q in CAFES
        )
        for username in ("alice", "bob"):
            user = User(username=username, email=f"{username}@example.com")
            user.set_password("password123")
            db.session.add(user)
        db.session.commit()
        print(f"Seeded {len(CAFES)} cafes and 2 users (alice, bob / password123).")


if __name__ == "__main__":
    seed()
