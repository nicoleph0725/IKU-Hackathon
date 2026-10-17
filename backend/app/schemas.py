"""Marshmallow schemas used to validate request bodies and query strings.

Responses are built with the models' to_dict() helpers; schemas here are input-only.
Validation failures raise marshmallow.ValidationError -> 422 JSON (see errors.py).
"""
from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema

rating_field = lambda **kw: fields.Integer(validate=validate.Range(min=1, max=5), **kw)  # noqa: E731


class RegisterSchema(Schema):
    username = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=30),
            validate.Regexp(r"^[A-Za-z0-9_]+$", error="Only letters, numbers and underscores."),
        ],
    )
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))


class LoginSchema(Schema):
    # Accepts either a username or an email address.
    login = fields.String(required=True, validate=validate.Length(min=1, max=255))
    password = fields.String(required=True, load_only=True)


class SettingsSchema(Schema):
    share_location = fields.Boolean(required=True)
    # TODO: more settings (e.g. default check-in duration, profile visibility).


class CafeSearchSchema(Schema):
    """Query string for GET /cafes. Unknown params (page, per_page) are ignored here."""

    class Meta:
        unknown = EXCLUDE

    lat = fields.Float(validate=validate.Range(min=-90, max=90))
    lng = fields.Float(validate=validate.Range(min=-180, max=180))
    max_distance_km = fields.Float(validate=validate.Range(min=0, min_inclusive=False, max=500))
    max_price = fields.Integer(validate=validate.Range(min=1, max=3))
    min_wifi = fields.Integer(validate=validate.Range(min=0, max=5))
    min_seats = fields.Integer(validate=validate.Range(min=0))
    max_busyness = fields.Float(validate=validate.Range(min=1, max=5))
    q = fields.String(validate=validate.Length(max=100))  # name/address text search
    sort = fields.String(validate=validate.OneOf(["distance", "rating", "busyness", "name"]))

    @validates_schema
    def check_location(self, data, **kwargs):
        has_lat, has_lng = "lat" in data, "lng" in data
        if has_lat != has_lng:
            raise ValidationError("lat and lng must be provided together", "lat")
        if not has_lat:
            if "max_distance_km" in data:
                raise ValidationError("max_distance_km requires lat and lng", "max_distance_km")
            if data.get("sort") == "distance":
                raise ValidationError("sort=distance requires lat and lng", "sort")


class BusynessReportSchema(Schema):
    level = fields.Integer(required=True, validate=validate.Range(min=1, max=5))


class ReviewSchema(Schema):
    rating = rating_field(required=True)
    space_rating = rating_field(allow_none=True)
    quietness_rating = rating_field(allow_none=True)
    wifi_rating = rating_field(allow_none=True)
    cost_rating = rating_field(allow_none=True)
    body = fields.String(load_default="", validate=validate.Length(max=2000))


class FriendRequestSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=1, max=30))


class CheckInSchema(Schema):
    cafe_id = fields.Integer(required=True)
    # How long until the check-in auto-expires. Max enforced in the view from config.
    duration_minutes = fields.Integer(validate=validate.Range(min=15))
