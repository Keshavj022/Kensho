"""Restaurant search & details via SerpApi's google_maps engine, normalized to a
consistent shape."""
from __future__ import annotations

import re
from typing import Any, Optional

from langchain_core.tools import tool

from ..config import settings
from . import _serpapi
from ._cache import cached

_TTL = settings.PLACES_CACHE_TTL_HOURS * 3600


def _price_level(price: Optional[str]) -> Optional[int]:
    """Map a price field to a 1–4 level. Handles symbol style ('$$', '₹₹') AND
    Indian range/number style ('₹800–1,000', '₹2,000+') by bucketing the midpoint."""
    if not price:
        return None
    s = price.strip()
    if not any(ch.isdigit() for ch in s):
        n = s.count("$") + s.count("₹")
        return min(4, n) if n else None
    nums = [int(m.replace(",", "")) for m in re.findall(r"\d[\d,]*", s)]
    if not nums:
        return None
    val = sum(nums) / len(nums)  # midpoint of a range, or the single value
    if val < 500:
        return 1
    if val < 1500:
        return 2
    if val < 3000:
        return 3
    return 4


def _open_now(open_state: Optional[str]) -> Optional[bool]:
    if not open_state:
        return None
    s = open_state.strip().lower()
    if s.startswith("open"):
        return True
    if s.startswith("closed") or "permanently closed" in s or "temporarily closed" in s:
        return False
    return None


def _normalize_maps(r: dict[str, Any]) -> dict[str, Any]:
    gps = r.get("gps_coordinates") or {}
    types = r.get("types") or ([r.get("type")] if r.get("type") else [])
    return {
        "id": r.get("place_id"),  # Google place_id (usable by the menu pipeline)
        "data_id": r.get("data_id"),
        "name": r.get("title"),
        "rating": r.get("rating"),
        "rating_count": r.get("reviews"),
        "price_level": _price_level(r.get("price")),
        "price_range": r.get("price"),  # raw, e.g. "₹800–1,000" — best for display in India
        "price_level_label": r.get("price"),
        "location": {"lat": gps.get("latitude"), "lng": gps.get("longitude")},
        "address": r.get("address"),
        "types": types,
        "primary_type": r.get("type"),
        "open_now": _open_now(r.get("open_state")),
        "phone": r.get("phone"),
        "website": r.get("website"),
        "summary": r.get("description"),
        "thumbnail": r.get("thumbnail"),
    }


@cached("maps.search", _TTL)
def _search_restaurants(
    query: Optional[str],
    location: Optional[str],
    lat: Optional[float],
    lng: Optional[float],
    radius: int,
    cuisine: Optional[str],
    price_level: Optional[int],
    open_now: Optional[bool],
    min_rating: Optional[float],
    dietary: Optional[str],
    max_results: int,
) -> dict[str, Any]:
    text_parts = [p for p in (cuisine, dietary, query) if p]
    q = (" ".join(text_parts) or "restaurants")
    if "restaurant" not in q.lower():
        q = f"{q} restaurants"
    if location:
        q = f"{q} in {location}"

    if not (text_parts or location or (lat is not None and lng is not None)):
        return {"status": "error", "message": "Provide a query/cuisine/location or lat+lng.", "restaurants": []}

    params: dict[str, Any] = {
        "engine": "google_maps",
        "type": "search",
        "q": q,
        "gl": settings.SERPAPI_GL,
        "hl": settings.SERPAPI_HL,
    }
    if lat is not None and lng is not None:
        params["ll"] = f"@{lat},{lng},14z"

    data = _serpapi.serpapi_search(params)
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message"), "restaurants": []}

    raw = data.get("local_results")
    if not raw and data.get("place_results"):
        raw = [data["place_results"]]
    restaurants = [_normalize_maps(r) for r in (raw or [])]

    if min_rating is not None:
        restaurants = [r for r in restaurants if (r.get("rating") or 0) >= float(min_rating)]
    if price_level is not None:
        restaurants = [r for r in restaurants if r.get("price_level") == int(price_level)]
    if open_now:
        restaurants = [r for r in restaurants if r.get("open_now") is True]
    restaurants = restaurants[: max(1, int(max_results or 20))]
    return {"status": "ok", "count": len(restaurants), "restaurants": restaurants}


@tool
def search_restaurants(
    query: Optional[str] = None,
    location: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: int = 5000,
    cuisine: Optional[str] = None,
    price_level: Optional[int] = None,
    open_now: Optional[bool] = None,
    min_rating: Optional[float] = None,
    dietary: Optional[str] = None,
    max_results: int = 20,
) -> dict[str, Any]:
    """Search for restaurants by text and/or location (Google Maps via SerpApi).

    Provide a text `query` (e.g. "ramen", "rooftop dinner") and/or a `location`
    string (e.g. "Kolkata", "Indiranagar Bangalore"), or `lat`/`lng` for a nearby
    search. Optional filters: `cuisine` (e.g. "bengali"), `price_level` (1-4),
    `open_now`, `min_rating` (0-5), `dietary` (e.g. "vegetarian"), `max_results`.
    Returns {status, count, restaurants:[{id(=place_id), name, rating, price_level,
    location{lat,lng}, address, types, open_now, ...}]}. The `id` is the place_id
    used by get_restaurant_details and the menu pipeline.
    """
    return _search_restaurants(
        query, location, lat, lng, radius, cuisine, price_level, open_now, min_rating, dietary, max_results
    )


@cached("maps.details", _TTL)
def _get_restaurant_details(place_id: str) -> dict[str, Any]:
    data = _serpapi.serpapi_search({"engine": "google_maps", "place_id": place_id, "gl": settings.SERPAPI_GL, "hl": settings.SERPAPI_HL})
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message")}
    pr = data.get("place_results") or {}
    if not pr:
        return {"status": "not_found", "message": "No place_results for this place_id"}
    norm = _normalize_maps(pr)
    norm["photo_urls"] = [u for u in [pr.get("thumbnail")] if u]
    norm["status"] = "ok"
    return norm


@tool
def get_restaurant_details(place_id: str) -> dict[str, Any]:
    """Get full details for one restaurant by its Google `place_id` (via SerpApi).

    Returns the normalized restaurant plus phone, website, summary, and a thumbnail.
    Call after search_restaurants to enrich a specific result. For menu photos use
    the menu pipeline (get_menu).
    """
    return _get_restaurant_details(place_id)
