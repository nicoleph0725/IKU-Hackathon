"""Reviews: one per user per cafe, overall rating + attribute ratings."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..errors import not_implemented

bp = Blueprint("reviews", __name__)


@bp.get("/cafes/<int:cafe_id>/reviews")
def list_reviews(cafe_id: int):
    # TODO: paginated reviews for the cafe, newest first.
    not_implemented("Listing reviews")


@bp.post("/cafes/<int:cafe_id>/reviews")
@jwt_required()
def create_review(cafe_id: int):
    # TODO: validate rating (1-5) + optional space/quietness/wifi/cost ratings + body, create Review, return 201.
    #       409 if the user already reviewed this cafe (there's a unique constraint on user_id+cafe_id).
    not_implemented("Creating reviews")


@bp.put("/reviews/<int:review_id>")
@jwt_required()
def update_review(review_id: int):
    # TODO: owner only (403 otherwise). Update the given fields.
    not_implemented("Updating reviews")


@bp.delete("/reviews/<int:review_id>")
@jwt_required()
def delete_review(review_id: int):
    # TODO: owner only (403 otherwise). Return 204.
    not_implemented("Deleting reviews")
