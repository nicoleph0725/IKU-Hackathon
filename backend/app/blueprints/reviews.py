"""Reviews: one per user per cafe, overall rating + optional attribute ratings."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select

from ..errors import APIError
from ..extensions import db
from ..models import Cafe, Review
from ..schemas import ReviewSchema
from ..utils import current_user_id, get_or_404, paginate

bp = Blueprint("reviews", __name__)


@bp.get("/cafes/<int:cafe_id>/reviews")
def list_reviews(cafe_id: int):
    get_or_404(Cafe, cafe_id, "Cafe")
    stmt = select(Review).where(Review.cafe_id == cafe_id).order_by(Review.created_at.desc(), Review.id.desc())
    # ?user_id= lets the frontend find "my review" for this cafe (to edit it).
    if (user_id := request.args.get("user_id", type=int)) is not None:
        stmt = stmt.where(Review.user_id == user_id)
    # TODO: ?sort=helpful once review upvotes exist.
    return jsonify(paginate(stmt, lambda r: r.to_dict()))


@bp.post("/cafes/<int:cafe_id>/reviews")
@jwt_required()
def create_review(cafe_id: int):
    get_or_404(Cafe, cafe_id, "Cafe")
    data = ReviewSchema().load(request.get_json(silent=True) or {})
    user_id = current_user_id()

    existing = db.session.scalar(select(Review.id).where(Review.cafe_id == cafe_id, Review.user_id == user_id))
    if existing:
        raise APIError(
            409, "already_reviewed", "You have already reviewed this cafe; edit your review instead",
            {"review_id": existing},
        )

    review = Review(cafe_id=cafe_id, user_id=user_id, **data)
    db.session.add(review)
    db.session.commit()
    return jsonify(review=review.to_dict()), 201


def get_own_review(review_id: int) -> Review:
    review = get_or_404(Review, review_id, "Review")
    if review.user_id != current_user_id():
        raise APIError(403, "forbidden", "You can only modify your own reviews")
    return review


@bp.put("/reviews/<int:review_id>")
@jwt_required()
def update_review(review_id: int):
    review = get_own_review(review_id)
    # partial=True: clients may send only the fields they want to change.
    data = ReviewSchema(partial=True).load(request.get_json(silent=True) or {})
    for key, value in data.items():
        setattr(review, key, value)
    db.session.commit()
    return jsonify(review=review.to_dict())


@bp.delete("/reviews/<int:review_id>")
@jwt_required()
def delete_review(review_id: int):
    review = get_own_review(review_id)
    db.session.delete(review)
    db.session.commit()
    return "", 204
