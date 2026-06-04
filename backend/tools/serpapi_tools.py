"""
SerpApi tools — travel metasearch (flights, hotels), shopping, and place photos.

TRAVEL IS SEARCH-ONLY: return the cheapest option, the provider offering it, a
deep link, and price context. No booking, no payments. Expensive calls are cached.
Degrades gracefully when SERPAPI_API_KEY is unset.
"""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool

from ..config import settings
from . import _serpapi
from ._cache import cached

_TTL = settings.SERPAPI_CACHE_TTL_HOURS * 3600
DEFAULT_CURRENCY = settings.DEFAULT_CURRENCY
_SORT_MAP = {"top": 1, "price": 2, "departure": 3, "arrival": 4, "duration": 5, "emissions": 6}


def _locale(extra: dict[str, Any]) -> dict[str, Any]:
    """Merge India locale (gl/hl) so results aren't US/USD by default."""
    return {"gl": settings.SERPAPI_GL, "hl": settings.SERPAPI_HL, **extra}


# ----------------------------------------------------------------- flights
def _normalize_flight(f: dict[str, Any]) -> dict[str, Any]:
    legs = f.get("flights", []) or []
    airlines = sorted({leg.get("airline") for leg in legs if leg.get("airline")})
    first, last = (legs[0] if legs else {}), (legs[-1] if legs else {})
    return {
        "price": f.get("price"),
        "total_duration_minutes": f.get("total_duration"),
        "stops": max(0, len(legs) - 1),
        "airlines": airlines,
        "departure": (first.get("departure_airport") or {}),
        "arrival": (last.get("arrival_airport") or {}),
        "carbon_emissions": (f.get("carbon_emissions") or {}).get("this_flight"),
        "booking_token": f.get("booking_token"),
        "departure_token": f.get("departure_token"),
        "legs": [
            {
                "airline": leg.get("airline"),
                "flight_number": leg.get("flight_number"),
                "from": (leg.get("departure_airport") or {}).get("id"),
                "to": (leg.get("arrival_airport") or {}).get("id"),
                "depart": (leg.get("departure_airport") or {}).get("time"),
                "arrive": (leg.get("arrival_airport") or {}).get("time"),
                "duration_minutes": leg.get("duration"),
            }
            for leg in legs
        ],
    }


@cached("serpapi.flights", _TTL)
def _search_flights(origin, destination, departure_date, return_date, adults, sort):
    params: dict[str, Any] = _locale({
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "type": 1 if return_date else 2,  # 1=round trip, 2=one way
        "sort_by": _SORT_MAP.get((sort or "price").lower(), 2),
        "currency": DEFAULT_CURRENCY,
        "adults": int(adults or 1),
    })
    if return_date:
        params["return_date"] = return_date
    data = _serpapi.serpapi_search(params)
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message"), "flights": []}

    best = [_normalize_flight(f) for f in data.get("best_flights", [])]
    others = [_normalize_flight(f) for f in data.get("other_flights", [])]
    # Google only marks "best" sometimes — merge so the UI always has results, sorted by price.
    combined = best + others
    combined.sort(key=lambda f: (f.get("price") is None, f.get("price") or 0))
    top = combined[:20]
    insights = data.get("price_insights") or {}
    return {
        "status": "ok",
        "currency": DEFAULT_CURRENCY,
        "cheapest": top[0] if top else None,
        "flights": top,
        "best_flights": best,
        "other_flights": others[:10],
        "price_insights": {
            "lowest_price": insights.get("lowest_price"),
            "price_level": insights.get("price_level"),
            "typical_price_range": insights.get("typical_price_range"),
        },
        "note": "Metasearch only — no booking. Use resolve_flight_booking_options(booking_token) for sellers.",
    }


@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    sort: str = "price",
) -> dict[str, Any]:
    """Search flights (metasearch, no booking) via Google Flights.

    `origin`/`destination` are IATA airport or city codes (e.g. "CCU", "DEL").
    `departure_date` and optional `return_date` are YYYY-MM-DD; omit return_date
    for one-way. `sort` is one of price/duration/departure/arrival/top. Returns
    {status, currency, cheapest, best_flights:[{price, airlines, stops,
    total_duration_minutes, departure, arrival, booking_token, legs}],
    price_insights:{lowest_price, price_level, typical_price_range}}. To get
    bookable sellers + a deep link for a chosen flight, pass its `booking_token`
    to resolve_flight_booking_options.
    """
    return _search_flights(origin, destination, departure_date, return_date, adults, sort)


def _booking_entry(entry: dict[str, Any]) -> dict[str, Any]:
    req = entry.get("booking_request") or {}
    return {
        "book_with": entry.get("book_with"),
        "price": entry.get("price"),
        "option_title": entry.get("option_title"),
        "deep_link": req.get("url"),
        "post_data": req.get("post_data"),
    }


@cached("serpapi.booking", _TTL)
def _resolve_flight_booking_options(booking_token, origin, destination, departure_date, return_date):
    params: dict[str, Any] = {
        "engine": "google_flights",
        "booking_token": booking_token,
        "currency": DEFAULT_CURRENCY,
    }
    # SerpApi requires the original search context alongside booking_token.
    if origin:
        params["departure_id"] = origin
    if destination:
        params["arrival_id"] = destination
    if departure_date:
        params["outbound_date"] = departure_date
    if return_date:
        params["return_date"] = return_date
        params["type"] = 1
    else:
        params["type"] = 2

    data = _serpapi.serpapi_search(params)
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message"), "options": []}

    options = []
    for opt in data.get("booking_options", []):
        entry = opt.get("together") or opt.get("departing") or {}
        if entry:
            options.append(_booking_entry(entry))
    options = [o for o in options if o.get("book_with")]
    options.sort(key=lambda o: (o.get("price") is None, o.get("price") or 0))
    return {
        "status": "ok",
        "currency": DEFAULT_CURRENCY,
        "cheapest": options[0] if options else None,
        "options": options,
        "note": "Metasearch only — surface 'book on {book_with}' with the deep_link; do not book.",
    }


@tool
def resolve_flight_booking_options(
    booking_token: str,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
) -> dict[str, Any]:
    """Resolve bookable sellers + deep links for a chosen flight (no booking).

    Pass the `booking_token` from a search_flights result, plus the SAME route
    context (`origin`, `destination`, `departure_date`, optional `return_date`)
    used in that search. Returns {status, cheapest, options:[{book_with, price,
    deep_link, post_data}]} — surface the cheapest seller as "book on X" with the
    deep link. booking_token is short-lived, so call this promptly after searching.
    """
    return _resolve_flight_booking_options(booking_token, origin, destination, departure_date, return_date)


# ----------------------------------------------------------------- hotels
def _cheapest_option(prop: dict[str, Any]) -> Optional[dict[str, Any]]:
    best = None
    for src in (prop.get("featured_prices") or []) + (prop.get("prices") or []):
        rate = (src.get("rate_per_night") or {}).get("extracted_lowest")
        if rate is None:
            continue
        cand = {
            "source": src.get("source"),
            "price_per_night": rate,
            "link": src.get("link"),
            "official": bool(src.get("official", False)),
        }
        if best is None or cand["price_per_night"] < best["price_per_night"]:
            best = cand
    return best


@cached("serpapi.hotels", _TTL)
def _search_hotels(location, check_in, check_out, guests):
    params = _locale({
        "engine": "google_hotels",
        "q": location,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": int(guests or 1),
        "currency": DEFAULT_CURRENCY,
    })
    data = _serpapi.serpapi_search(params)
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message"), "hotels": []}

    hotels = []
    for prop in data.get("properties", []):
        cheapest = _cheapest_option(prop)
        hotels.append(
            {
                "name": prop.get("name"),
                "rating": prop.get("overall_rating"),
                "hotel_class": prop.get("hotel_class"),
                "price_per_night": (prop.get("rate_per_night") or {}).get("extracted_lowest"),
                "total_rate": (prop.get("total_rate") or {}).get("extracted_lowest"),
                "cheapest_provider": cheapest,
                "gps": prop.get("gps_coordinates"),
                "link": prop.get("link"),
            }
        )
    hotels.sort(key=lambda h: (h.get("price_per_night") is None, h.get("price_per_night") or 0))
    return {
        "status": "ok",
        "currency": DEFAULT_CURRENCY,
        "count": len(hotels),
        "cheapest": hotels[0] if hotels else None,
        "hotels": hotels,
        "note": "Metasearch only — no booking.",
    }


@tool
def search_hotels(location: str, check_in: str, check_out: str, guests: int = 1) -> dict[str, Any]:
    """Search hotels (metasearch, no booking) via Google Hotels.

    `location` is a city/area/landmark (e.g. "Kolkata", "near Howrah Station").
    `check_in`/`check_out` are YYYY-MM-DD. Returns {status, currency, count,
    cheapest, hotels:[{name, rating, price_per_night, total_rate,
    cheapest_provider:{source, price_per_night, link, official}, gps}]} sorted
    cheapest-first. Surface the cheapest provider + its link as price context.
    """
    return _search_hotels(location, check_in, check_out, guests)


# ----------------------------------------------------------------- shopping
@cached("serpapi.shopping", _TTL)
def _search_products(query, max_results):
    data = _serpapi.serpapi_search(
        _locale({"engine": "google_shopping", "q": query, "location": settings.SERPAPI_LOCATION})
    )
    if data.get("_error"):
        return {"status": data["_error"], "message": data.get("_message"), "products": []}
    products = []
    for r in (data.get("shopping_results") or [])[: max(1, int(max_results or 20))]:
        products.append(
            {
                "title": r.get("title"),
                "price": r.get("extracted_price"),
                "price_label": r.get("price"),  # already locale-formatted, e.g. "₹26,999"
                "source": r.get("source"),  # merchant
                "link": r.get("product_link") or r.get("link"),
                "rating": r.get("rating"),
                "reviews": r.get("reviews"),
                "thumbnail": r.get("thumbnail"),
                "delivery": r.get("delivery"),
            }
        )
    return {"status": "ok", "currency": DEFAULT_CURRENCY, "count": len(products), "products": products}


@tool
def search_products(query: str, max_results: int = 20) -> dict[str, Any]:
    """Search shopping products via Google Shopping.

    `query` is a product search (e.g. "noise cancelling headphones under 10000").
    Returns {status, count, products:[{title, price(number), source(merchant),
    link, rating, reviews}]}. Use for the shopping domain.
    """
    return _search_products(query, max_results)


# ----------------------------------------------------------------- place photos (menu pipeline)
@cached("serpapi.maps_photos", _TTL)
def _get_place_photos(place_id):
    # google_maps_photos needs a Maps data_id, NOT a place_id. Resolve it first.
    lookup = _serpapi.serpapi_search({"engine": "google_maps", "place_id": place_id})
    if lookup.get("_error"):
        return {"status": lookup["_error"], "message": lookup.get("_message"), "photos": []}
    data_id = (lookup.get("place_results") or {}).get("data_id")
    if not data_id:
        return {"status": "no_data_id", "message": "Could not resolve a Maps data_id", "photos": []}

    photos_resp = _serpapi.serpapi_search({"engine": "google_maps_photos", "data_id": data_id})
    if photos_resp.get("_error"):
        return {"status": photos_resp["_error"], "message": photos_resp.get("_message"), "photos": []}
    urls = [p.get("image") for p in photos_resp.get("photos", []) if p.get("image")]
    return {"status": "ok", "data_id": data_id, "count": len(urls), "photos": urls}


@tool
def get_place_photos(place_id: str) -> dict[str, Any]:
    """Fetch user-posted photo URLs for a place (used by the menu pipeline).

    Takes a Google `place_id`, resolves its Maps data_id, and returns
    {status, count, photos:[image_url,...]} of user-posted photos (unlabeled —
    the menu pipeline classifies which are menu images). Not for general display.
    """
    return _get_place_photos(place_id)
