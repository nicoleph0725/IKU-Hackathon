"""Consistent JSON error responses.

Every error looks like:
    {"error": {"code": "not_found", "message": "Cafe not found", "details": {...}}}
"""
import logging

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from .extensions import db, jwt

log = logging.getLogger(__name__)


class APIError(Exception):
    """Raise anywhere in a view to return a JSON error."""

    def __init__(self, status: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def error_response(status: int, code: str, message: str, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(e: APIError):
        return error_response(e.status, e.code, e.message, e.details)

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError):
        return error_response(422, "validation_error", "Invalid input", e.messages)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e: IntegrityError):
        db.session.rollback()
        log.warning("Integrity error: %s", e.orig)
        return error_response(409, "conflict", "Request conflicts with existing data")

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        code = (e.name or "error").lower().replace(" ", "_")
        return error_response(e.code or 500, code, e.description or e.name)

    @app.errorhandler(Exception)
    def handle_unexpected(e: Exception):
        db.session.rollback()
        log.exception("Unhandled error")
        return error_response(500, "internal_error", "Something went wrong")

    # --- JWT errors (missing / invalid / expired token) -> 401 ---------------
    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response(401, "unauthorized", "Missing or malformed access token")

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response(401, "invalid_token", "Invalid access token")

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response(401, "token_expired", "Access token has expired, please log in again")


def not_implemented(what: str = "This endpoint"):
    """Placeholder for endpoints the team hasn't built yet. Remove once implemented."""
    raise APIError(501, "not_implemented", f"{what} is not implemented yet")
