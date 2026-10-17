"""Flask backend. Empty for now: we'll add API routes here as we build features."""
from flask import Flask, jsonify
from flask_cors import CORS
from db import get_conn

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    """Quick check that the backend is running."""
    return {"status": "ok"}

@app.get("/api/db-health")
def db_health():
    """Check that the database connection works."""
    with get_conn() as conn:
        row = conn.execute("SELECT 1 AS ok").fetchone()
    return jsonify(row)


@app.get("/api/cafes")
def list_cafes():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM cafes").fetchall()
    return jsonify(rows)