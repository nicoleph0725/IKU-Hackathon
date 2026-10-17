"""Database models.

checkins and busyness_reports are TimescaleDB hypertables partitioned on `time` (see the
initial migration). TimescaleDB requires primary keys on hypertables to include `time`,
so they use composite keys instead of an `id`.

After changing a model: `flask db migrate -m "what changed"` then `flask db upgrade`.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    share_location = db.Column(db.Boolean, nullable=False, server_default="false", default=False)  # opt-in

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self) -> dict:
        """Safe to show to other users."""
        return {"id": self.id, "username": self.username}

    def to_private_dict(self) -> dict:
        """Only for the user themself."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "share_location": self.share_location,
            "created_at": iso(self.created_at),
        }


class Cafe(db.Model):
    __tablename__ = "cafes"
    __table_args__ = (
        CheckConstraint("price_level BETWEEN 1 AND 3", name="ck_cafes_price_level"),
        CheckConstraint("wifi_quality BETWEEN 0 AND 5", name="ck_cafes_wifi_quality"),
        CheckConstraint("seating_capacity >= 0", name="ck_cafes_seating_capacity"),
        CheckConstraint("lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180", name="ck_cafes_coords"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    price_level = db.Column(db.SmallInteger, nullable=False)              # 1-3
    seating_capacity = db.Column(db.Integer, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False, default=False)
    wifi_quality = db.Column(db.SmallInteger, nullable=False, default=0)  # 0 = none .. 5 = excellent
    opening_hours = db.Column(JSONB, nullable=True)  # e.g. {"mon": [["08:00", "18:00"]], "sun": []}
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    # TODO: add a to_dict() for API responses (see User.to_private_dict for the pattern).


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "cafe_id", name="uq_reviews_user_cafe"),  # one review per user per cafe
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        CheckConstraint("space_rating BETWEEN 1 AND 5", name="ck_reviews_space"),
        CheckConstraint("quietness_rating BETWEEN 1 AND 5", name="ck_reviews_quietness"),
        CheckConstraint("wifi_rating BETWEEN 1 AND 5", name="ck_reviews_wifi"),
        CheckConstraint("cost_rating BETWEEN 1 AND 5", name="ck_reviews_cost"),
        Index("ix_reviews_cafe_created", "cafe_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.SmallInteger, nullable=False)
    space_rating = db.Column(db.SmallInteger)      # attribute ratings are optional
    quietness_rating = db.Column(db.SmallInteger)
    wifi_rating = db.Column(db.SmallInteger)
    cost_rating = db.Column(db.SmallInteger)
    body = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True, onupdate=utcnow)

    user = db.relationship("User")

    # TODO: add a to_dict() for API responses.


class Friendship(db.Model):
    """A friend request: status 'pending' -> 'accepted'. Declining can just delete the row.

    The unique (LEAST, GREATEST) index stops A->B and B->A from both existing.
    """

    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint("requester_id <> addressee_id", name="ck_friendships_not_self"),
        CheckConstraint("status IN ('pending', 'accepted')", name="ck_friendships_status"),
        Index("ix_friendships_addressee_status", "addressee_id", "status"),
        Index("ix_friendships_requester_status", "requester_id", "status"),
        Index(
            "uq_friendships_pair",
            text("LEAST(requester_id, addressee_id)"),
            text("GREATEST(requester_id, addressee_id)"),
            unique=True,
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    requester = db.relationship("User", foreign_keys=[requester_id])
    addressee = db.relationship("User", foreign_keys=[addressee_id])


class CheckIn(db.Model):
    """Hypertable. Opt-in presence at a cafe (not GPS).

    Active = checked_out_at IS NULL AND expires_at > now(). Old rows are kept as history.
    """

    __tablename__ = "checkins"
    __table_args__ = (Index("ix_checkins_cafe_time", "cafe_id", "time"),)

    time = db.Column(db.DateTime(timezone=True), primary_key=True, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    checked_out_at = db.Column(db.DateTime(timezone=True), nullable=True)

    cafe = db.relationship("Cafe")
    user = db.relationship("User")


class BusynessReport(db.Model):
    """Hypertable. 'How busy is it right now?' reports, level 1 (empty) .. 5 (packed)."""

    __tablename__ = "busyness_reports"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 5", name="ck_busyness_level"),
        Index("ix_busyness_cafe_time", "cafe_id", "time"),
    )

    time = db.Column(db.DateTime(timezone=True), primary_key=True, default=utcnow)
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level = db.Column(db.SmallInteger, nullable=False)
