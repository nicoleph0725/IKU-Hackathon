"""Flask backend. Empty for now: we'll add API routes here as we build features."""
from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
from db import get_conn
from gemini import GEMINI_KEY, PREFERENCE_TEXT, rank_cafes_with_gemini
from places import MAP_KEY, get_photo_uri, public_cafe, search_get_cafes

app = Flask(__name__)
CORS(app)


#################################
# Routes
#################################

@app.get("/api/places/cafes")
def google_cafes():
    """Cafes near SEARCH_CENTER for the map pins."""
    if not MAP_KEY:
        return jsonify(error="MAP_KEY is missing from backend/.env"), 500
    try:
        return jsonify([public_cafe(c) for c in search_get_cafes()])
    except RuntimeError as err:
        return jsonify(error=f"Google Places error: {err}"), 502


@app.post("/api/cafes/recommend")
def recommend_cafes():
    """Cafes ranked by the student's preferences.

    Body (all optional): {"space": "any|some|lots", "budget": "any|1|2|3",
                          "quietness": "any|quiet|very_quiet", "wifi": "any|needed|fast",
                          "open_now": bool, "notes": str}
    Price and "open now" come straight from Google, so they're hard filters.
    Space, quietness and wifi aren't in Google's data, so Gemini judges them from reviews.
    """
    if not MAP_KEY or not GEMINI_KEY:
        return jsonify(error="MAP_KEY and GEMINI_KEY must be set in backend/.env"), 500

    prefs = request.get_json(silent=True) or {}
    notes = str(prefs.get("notes", "")).strip()[:300]

    try:
        cafes = search_get_cafes()
    except RuntimeError as err:
        return jsonify(error=f"Google Places error: {err}"), 502

    # Hard filters (real data from Google). Cafes with an unknown price are kept.
    budget = str(prefs.get("budget", "any"))
    if budget in ("1", "2", "3"):
        cafes = [c for c in cafes if c["price_level"] is None or c["price_level"] <= int(budget)]
    if prefs.get("open_now"):
        cafes = [c for c in cafes if c["open_now"]]

    wants = [PREFERENCE_TEXT[field][prefs[field]]
             for field in PREFERENCE_TEXT if prefs.get(field) in PREFERENCE_TEXT[field]]
    if (not wants and not notes) or not cafes:
        # Nothing for Gemini to judge: just return the filtered cafes by Google rating.
        cafes = sorted(cafes, key=lambda c: c["rating"] or 0, reverse=True)
        return jsonify([public_cafe(c) for c in cafes])

    try:
        scores = rank_cafes_with_gemini(cafes, wants, notes)
    except (RuntimeError, KeyError, ValueError) as err:
        return jsonify(error=f"Gemini error: {err}"), 502

    ranked = []
    for cafe in cafes:
        if cafe["id"] in scores:
            ranked.append({**public_cafe(cafe), **scores[cafe["id"]]})
    ranked.sort(key=lambda c: c["score"], reverse=True)
    return jsonify(ranked[:10])  # top 10


@app.get("/api/places/photo")
def google_photo():
    """Redirect to a cafe photo. Use as <img src="/api/places/photo?name=...">.

    Going through the backend keeps MAP_KEY out of image URLs in the browser.
    """
    name = request.args.get("name", "")
    if not (name.startswith("places/") and "/photos/" in name):
        return jsonify(error="Invalid photo name"), 400

    photo_uri = get_photo_uri(name)
    if photo_uri is None:
        return jsonify(error="Photo not found"), 404
    return redirect(photo_uri)


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
