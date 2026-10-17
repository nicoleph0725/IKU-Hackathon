"""Marshmallow schemas for validating request input.

Usage in a view:  data = MySchema().load(request.get_json(silent=True) or {})
Invalid input raises ValidationError, which errors.py turns into a 422 JSON response.
"""
from marshmallow import Schema, fields, validate


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
    login = fields.String(required=True)  # username or email
    password = fields.String(required=True, load_only=True)


# TODO: add schemas as you build each feature, e.g.
#   SettingsSchema        {share_location: bool}
#   CafeSearchSchema      query params: lat, lng, max_distance_km, max_price, min_wifi, min_seats, max_busyness, sort
#   ReviewSchema          rating (1-5, required), space/quietness/wifi/cost ratings (1-5, optional), body
#   BusynessReportSchema  {level: 1-5}
#   FriendRequestSchema   {username}
#   CheckInSchema         {cafe_id, duration_minutes?}
