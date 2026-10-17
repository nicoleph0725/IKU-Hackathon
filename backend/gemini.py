"""Gemini: ranking cafes against a student's preferences, using the cafes' reviews."""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
# Flash-lite answered in ~4s in testing; gemini-3.8-flash ranks a bit better but takes ~9s+.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


# What each preference option means, in words Gemini can use.
PREFERENCE_TEXT = {
    "space": {"some": "enough seats to sit and work", "lots": "lots of space and big tables"},
    "quietness": {"quiet": "fairly quiet", "very_quiet": "very quiet, good for focusing"},
    "wifi": {"needed": "has wifi", "fast": "fast, reliable wifi for video calls"},
}

GEMINI_RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "STRING"},
            "score": {"type": "INTEGER"},
            "reason": {"type": "STRING"},
        },
        "required": ["id", "score", "reason"],
    },
}


def rank_cafes_with_gemini(cafes, wants, notes):
    """Ask Gemini to score each cafe 0-100 against the student's wishes, using the cafes' reviews.

    Returns {cafe_id: {"score": int, "reason": str}}. Raises RuntimeError if Gemini fails.
    """
    candidates = [
        {"id": c["id"], "name": c["name"], "price_level": c["price_level"], "rating": c["rating"],
         "summary": c["summary"], "reviews": c["reviews"]}
        for c in cafes
    ]
    prompt = (
        "You help students choose a cafe to study in.\n"
        f"The student wants: {'; '.join(wants) or 'any good study cafe'}.\n"
        + (f"Extra notes from the student: {notes}\n" if notes else "")
        + "\nScore EVERY cafe below from 0 to 100 for how well it matches.\n"
        "Rules:\n"
        "- Use ONLY the summaries and reviews given. Do not use outside knowledge.\n"
        "- If the reviews don't mention something the student wants, treat it as unknown (neutral), "
        "not as bad, and say it's unknown in the reason.\n"
        "- reason: one short sentence (max 25 words) quoting or paraphrasing the evidence.\n\n"
        f"Cafes:\n{json.dumps(candidates)}"
    )
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            # Forces Gemini to reply with JSON in exactly this shape.
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": GEMINI_RESPONSE_SCHEMA},
        },
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(resp.json().get("error", {}).get("message", resp.text))

    scores = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
    known_ids = {c["id"] for c in cafes}
    # Ignore any id Gemini made up.
    return {s["id"]: {"score": max(0, min(100, s["score"])), "reason": s["reason"]}
            for s in scores if s["id"] in known_ids}
