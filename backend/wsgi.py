"""Entry point: `flask run` picks this up automatically (or point a WSGI server at wsgi:app)."""
from app import create_app

app = create_app()
