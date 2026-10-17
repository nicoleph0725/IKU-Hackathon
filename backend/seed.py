"""Seed the database with demo data so the app looks alive immediately.

Usage (from backend/, venv active, after `flask db upgrade`):
    python seed.py

WARNING: wipes all existing rows first. Cafes are fictional, placed around real London areas.
Demo logins (password for all: password123): alice, bob, charlie, dana
"""
import random
from datetime import timedelta

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import BusynessReport, Cafe, CheckIn, Friendship, Review, User, utcnow

random.seed(42)  # reproducible demo data

WEEKDAY = [["08:00", "19:00"]]
LATE = [["08:00", "22:00"]]
WEEKEND = [["09:00", "18:00"]]


def hours(weekday=WEEKDAY, sat=WEEKEND, sun=WEEKEND):
    return {"mon": weekday, "tue": weekday, "wed": weekday, "thu": weekday, "fri": weekday, "sat": sat, "sun": sun}


# name, address, lat, lng, price, seats, has_wifi, wifi_quality, opening hours
CAFES = [
    ("The Reading Room", "12 Gower St, Bloomsbury, WC1E", 51.5222, -0.1316, 2, 60, True, 5, hours(LATE)),
    ("Bean & Bookmark", "48 Store St, Bloomsbury, WC1E", 51.5199, -0.1310, 1, 35, True, 4, hours()),
    ("Kings Cross Commons", "3 Granary Sq, King's Cross, N1C", 51.5357, -0.1255, 2, 120, True, 4, hours(LATE, LATE, WEEKEND)),
    ("Quiet Quarter", "21 Exmouth Market, Clerkenwell, EC1R", 51.5262, -0.1086, 3, 25, True, 5, hours()),
    ("Shoreditch Grind House", "77 Old St, Shoreditch, EC1V", 51.5256, -0.0876, 2, 45, True, 3, hours(LATE, LATE, LATE)),
    ("Southbank Steam", "9 Belvedere Rd, South Bank, SE1", 51.5055, -0.1160, 3, 80, True, 4, hours(LATE)),
    ("Borough Brew Lab", "14 Stoney St, Borough, SE1", 51.5051, -0.0910, 2, 30, True, 2, hours(WEEKDAY, WEEKEND, [])),
    ("Camden Cuppa", "102 Camden High St, Camden, NW1", 51.5390, -0.1426, 1, 40, True, 3, hours()),
    ("Marylebone Matcha", "55 Marylebone High St, W1U", 51.5203, -0.1520, 3, 20, True, 4, hours(WEEKDAY, WEEKEND, [])),
    ("Soho Study Spot", "31 Greek St, Soho, W1D", 51.5137, -0.1310, 2, 28, True, 3, hours(LATE, LATE, WEEKEND)),
    ("Covent Garden Corner", "6 Neal St, Covent Garden, WC2H", 51.5140, -0.1260, 3, 50, False, 0, hours()),
    ("Angel Espresso", "200 Upper St, Islington, N1", 51.5380, -0.1030, 2, 55, True, 4, hours()),
    ("Brixton Beans", "18 Coldharbour Ln, Brixton, SW9", 51.4626, -0.1123, 1, 65, True, 3, hours(LATE, LATE, LATE)),
    ("Whitechapel Works", "88 Whitechapel Rd, E1", 51.5171, -0.0627, 1, 90, True, 5, hours(LATE)),
    ("Canary Wharf Coffee Co.", "1 Canada Sq, Canary Wharf, E14", 51.5049, -0.0195, 3, 150, True, 5, hours(WEEKDAY, [], [])),
]

USERS = [
    ("alice", "alice@example.com", False),   # sharing off: friends can't see her
    ("bob", "bob@example.com", True),
    ("charlie", "charlie@example.com", True),
    ("dana", "dana@example.com", True),
]

REVIEW_SNIPPETS = [
    "Plenty of plugs and nobody minds if you stay all afternoon.",
    "Great flat white, but it gets loud around lunchtime.",
    "Wifi was fast enough for video calls. Will be back.",
    "Bit pricey, but the big tables make up for it.",
    "Cosy and quiet in the mornings, perfect for revision.",
    "Hard to find a seat after 11am. Come early.",
    "Friendly staff, decent pastries, music a bit loud.",
    "My go-to spot for essay writing. Huge windows.",
]


def seed():
    app = create_app()
    with app.app_context():
        print("Clearing existing data...")
        db.session.execute(text(
            "TRUNCATE busyness_reports, checkins, reviews, friendships, cafes, users RESTART IDENTITY CASCADE"
        ))

        cafes = [
            Cafe(name=n, address=a, lat=lat, lng=lng, price_level=p, seating_capacity=s,
                 has_wifi=w, wifi_quality=q, opening_hours=h)
            for n, a, lat, lng, p, s, w, q, h in CAFES
        ]
        db.session.add_all(cafes)

        users = []
        for username, email, share in USERS:
            u = User(username=username, email=email, share_location=share)
            u.set_password("password123")
            users.append(u)
        db.session.add_all(users)
        db.session.flush()  # assign ids
        alice, bob, charlie, dana = users
        now = utcnow()

        # Friendships: alice <-> bob, alice <-> charlie accepted; dana -> alice pending; bob <-> charlie accepted.
        db.session.add_all([
            Friendship(requester_id=alice.id, addressee_id=bob.id, status="accepted", accepted_at=now),
            Friendship(requester_id=charlie.id, addressee_id=alice.id, status="accepted", accepted_at=now),
            Friendship(requester_id=bob.id, addressee_id=charlie.id, status="accepted", accepted_at=now),
            Friendship(requester_id=dana.id, addressee_id=alice.id, status="pending"),
        ])

        # Reviews: each user reviews a random subset of cafes, skewed by wifi quality.
        n_reviews = 0
        for user in users:
            for cafe in random.sample(cafes, 9):
                base = 3 + (cafe.wifi_quality >= 4) - (cafe.price_level == 3) * random.choice([0, 1])
                r = lambda off=0: max(1, min(5, base + off + random.choice([-1, 0, 0, 1])))  # noqa: E731
                db.session.add(Review(
                    user_id=user.id, cafe_id=cafe.id,
                    rating=r(),
                    space_rating=r(1 if cafe.seating_capacity > 60 else -1),
                    quietness_rating=r(random.choice([-1, 0, 1])),
                    wifi_rating=max(1, cafe.wifi_quality) if cafe.has_wifi else 1,
                    cost_rating=r(2 - cafe.price_level),
                    body=random.choice(REVIEW_SNIPPETS),
                    created_at=now - timedelta(days=random.randint(1, 60), minutes=random.randint(0, 1440)),
                ))
                n_reviews += 1

        # Busyness reports over the last 12 hours (some within the last 60 min -> "current").
        n_reports = 0
        for cafe in cafes:
            typical = random.randint(1, 5)
            for user in users:
                for _ in range(random.randint(1, 4)):
                    minutes_ago = random.randint(1, 12 * 60)
                    db.session.add(BusynessReport(
                        time=now - timedelta(minutes=minutes_ago, seconds=random.randint(0, 59)),
                        cafe_id=cafe.id, user_id=user.id,
                        level=max(1, min(5, typical + random.choice([-1, 0, 0, 1]))),
                    ))
                    n_reports += 1
            # Most cafes get a fresh report so "current busyness" is populated; leave a few unknown.
            if cafe.id % 5 != 0:
                db.session.add(BusynessReport(
                    time=now - timedelta(minutes=random.randint(2, 50)), cafe_id=cafe.id,
                    user_id=random.choice(users).id, level=typical,
                ))
                n_reports += 1

        # Active check-ins: bob and charlie are studying right now (both share). Alice is checked
        # in too but has sharing off, so nobody should see her. Plus some past check-in history.
        db.session.add_all([
            CheckIn(time=now - timedelta(minutes=40), user_id=bob.id, cafe_id=cafes[0].id,
                    expires_at=now + timedelta(hours=2)),
            CheckIn(time=now - timedelta(minutes=15), user_id=charlie.id, cafe_id=cafes[2].id,
                    expires_at=now + timedelta(hours=3)),
            CheckIn(time=now - timedelta(minutes=5), user_id=alice.id, cafe_id=cafes[3].id,
                    expires_at=now + timedelta(hours=3)),
        ])
        for user in users:
            for day in range(1, 8):
                start = now - timedelta(days=day, hours=random.randint(1, 8))
                db.session.add(CheckIn(time=start, user_id=user.id, cafe_id=random.choice(cafes).id,
                                       expires_at=start + timedelta(hours=3),
                                       checked_out_at=start + timedelta(hours=random.randint(1, 3))))

        db.session.commit()
        print(f"Seeded {len(cafes)} cafes, {len(users)} users, {n_reviews} reviews, "
              f"{n_reports} busyness reports, check-ins and friendships.")
        print("Log in as alice / password123 (or bob, charlie, dana).")


if __name__ == "__main__":
    seed()
