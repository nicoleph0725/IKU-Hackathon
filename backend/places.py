"""Google Places: finding cafes near KCL Strand and fetching their photos."""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
MAP_KEY = os.getenv("MAP_KEY", "").strip()


#################################
# Google Places settings
#################################

# Docs: https://developers.google.com/maps/documentation/places/web-service/nearby-search
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Default search centre when the user hasn't searched for a location: King's College London, Strand campus.
SEARCH_CENTER = {"latitude": 51.5115, "longitude": -0.1160}
SEARCH_RADIUS_METRES = 1000

# Which places count as cafes. Google gives each place one main ("primary") type plus a list of other types.
# Places whose main type is one of these are always cafes:
CAFE_TYPES = ["cafe", "coffee_shop", "tea_house"]
# Places whose main type is one of these count only if Google also tags them as a cafe/coffee shop.
# That lets in Pret (sandwich_shop) and GAIL's (bakery), but not takeaway-only bakeries or bagel shops.
MAYBE_CAFE_TYPES = ["sandwich_shop", "bakery"]
# Places we don't want, matched against the place name (lowercase): chains, and places that
# Google calls cafes but aren't somewhere to sit and study.
EXCLUDED_NAMES = ["greggs", "subway", "afternoon tea", "kiosk", "shelter"]
# Hide places with fewer Google reviews than this: empty/duplicate listings and tiny kiosks.
MIN_REVIEWS = 5

# Only ask Google for the fields we use (you're billed by which fields you request).
PLACES_FIELDS = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.currentOpeningHours.openNow",
    "places.photos",
    "places.priceLevel",
    "places.editorialSummary",
    "places.primaryType",
    "places.types",
    # Reviews are what Gemini reads to judge space, quietness and wifi.
    # Note: asking for reviews puts the request in Google's most expensive Places tier.
    "places.reviews",
])

# Google's price levels -> 1 (£) .. 4 (££££)
PRICE_LEVELS = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}

# Every Places request costs money, so reuse results for a few minutes.
CACHE_SECONDS = 10 * 60
_places_cache = {}  # (lat, lng) rounded -> {"time": ..., "cafes": [...]}


#################################
# Helper functions
#################################

def search_get_cafes(lat=SEARCH_CENTER["latitude"], lng=SEARCH_CENTER["longitude"]):
    """Up to ~40 cafes around (lat, lng) from Google Places, as a list of dicts. Defaults to KCL Strand.

    Raises RuntimeError if Google returns an error.
    """
    # Rounded to ~10 m so searching the same place twice reuses the cached result.
    cache_key = (round(lat, 4), round(lng, 4))
    cached = _places_cache.get(cache_key)
    if cached and time.time() - cached["time"] < CACHE_SECONDS:
        return cached["cafes"]

    # Google returns at most 20 places per search, so we do two and combine them:
    # the 20 closest (cafes right next to you) and the 20 most popular within the radius
    # (well-known cafes a bit further away). Note: this costs two Places requests per new area.
    places = []
    for rank in ["DISTANCE", "POPULARITY"]:
        resp = requests.post(
            PLACES_NEARBY_URL,
            headers={"X-Goog-Api-Key": MAP_KEY, "X-Goog-FieldMask": PLACES_FIELDS},
            json={
                # primary type = what the place mainly is (filters out restaurants/shops that also sell coffee)
                "includedPrimaryTypes": CAFE_TYPES + MAYBE_CAFE_TYPES,
                "maxResultCount": 20,  # Google's maximum for nearby search
                "rankPreference": rank,
                "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lng},
                                                   "radius": SEARCH_RADIUS_METRES}},
            },
            timeout=15,
        )
        if not resp.ok:
            raise RuntimeError(resp.json().get("error", {}).get("message", resp.text))
        places += resp.json().get("places", [])

    cafes = []
    seen_ids = set()
    for place in places:
        if place["id"] in seen_ids or not _is_cafe(place):  # skip cafes found by both searches
            continue
        seen_ids.add(place["id"])
        photo = (place.get("photos") or [None])[0]
        cafes.append({
            "id": place["id"],
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"],
            "rating": place.get("rating"),
            "rating_count": place.get("userRatingCount", 0),
            "open_now": place.get("currentOpeningHours", {}).get("openNow"),
            "price_level": PRICE_LEVELS.get(place.get("priceLevel")),
            "summary": place.get("editorialSummary", {}).get("text"),
            # Only used by Gemini; removed before sending cafes to the browser.
            "reviews": [r.get("text", {}).get("text", "")[:400] for r in place.get("reviews", [])],
            # Not a URL: pass it to /api/places/photo to get the image.
            "photo_name": photo["name"] if photo else None,
            # Google requires showing who took the photo.
            "photo_author": photo["authorAttributions"][0]["displayName"]
            if photo and photo.get("authorAttributions") else None,
            # TODO: busyness. The Places API does not provide live busyness ("popular times").
        })

    # Forget expired searches so the cache doesn't grow forever.
    now = time.time()
    for key in [k for k, v in _places_cache.items() if now - v["time"] >= CACHE_SECONDS]:
        del _places_cache[key]
    _places_cache[cache_key] = {"time": now, "cafes": cafes}
    return cafes


def _is_cafe(place):
    """True if a Google place is a cafe we want to show (see CAFE_TYPES, EXCLUDED_NAMES and MIN_REVIEWS)."""
    name = place.get("displayName", {}).get("text", "").lower()
    if any(excluded in name for excluded in EXCLUDED_NAMES):
        return False
    if place.get("userRatingCount", 0) < MIN_REVIEWS:
        return False
    if place.get("primaryType") in CAFE_TYPES:
        return True
    return (place.get("primaryType") in MAYBE_CAFE_TYPES
            and bool({"cafe", "coffee_shop"} & set(place.get("types", []))))


def public_cafe(cafe):
    """A cafe without the fields the browser doesn't need."""
    return {k: v for k, v in cafe.items() if k != "reviews"}


def get_photo_uri(name):
    """The image URL for a Places photo name, or None if Google can't find it."""
    resp = requests.get(
        f"https://places.googleapis.com/v1/{name}/media",
        params={"maxWidthPx": 400, "skipHttpRedirect": "true", "key": MAP_KEY},
        timeout=15,
    )
    if not resp.ok:
        return None
    return resp.json()["photoUri"]
