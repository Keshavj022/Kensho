"""Milestone 3 — tools parse real API shapes (mocked) and degrade gracefully."""
from __future__ import annotations

import httpx
import respx

from backend.config import settings
from backend.tools import kg_tools, places_tools, rag_tools, search_tools, serpapi_tools

SERP = "https://serpapi.com/search"


@respx.mock
def test_search_restaurants_via_serpapi_maps(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    payload = {
        "local_results": [
            {
                "title": "Bhojohori Manna",
                "place_id": "PID1",
                "data_id": "DID1",
                "rating": 4.4,
                "reviews": 1200,
                "price": "$$",
                "gps_coordinates": {"latitude": 22.5, "longitude": 88.36},
                "address": "Kolkata, WB",
                "type": "Bengali restaurant",
                "types": ["restaurant"],
                "open_state": "Open ⋅ Closes 11 PM",
            }
        ]
    }
    respx.get(SERP).mock(return_value=httpx.Response(200, json=payload))
    out = places_tools.search_restaurants.invoke({"query": "bengali", "location": "Kolkata"})
    assert out["status"] == "ok" and out["count"] == 1
    r = out["restaurants"][0]
    assert r["id"] == "PID1" and r["data_id"] == "DID1"
    assert r["name"].startswith("Bhojohori")
    assert r["price_level"] == 2  # "$$" -> 2
    assert r["open_now"] is True
    assert r["location"] == {"lat": 22.5, "lng": 88.36}


def test_search_restaurants_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", None)
    out = places_tools.search_restaurants.invoke({"query": "x", "location": "y"})
    assert out["status"] == "not_configured" and out["restaurants"] == []


@respx.mock
def test_search_flights_two_call_flow(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    flights = {
        "best_flights": [
            {
                "price": 8500,
                "total_duration": 150,
                "flights": [
                    {
                        "airline": "IndiGo",
                        "flight_number": "6E-123",
                        "departure_airport": {"id": "CCU", "time": "2026-07-10 06:00"},
                        "arrival_airport": {"id": "DEL", "time": "2026-07-10 08:30"},
                        "duration": 150,
                    }
                ],
                "booking_token": "BT1",
            }
        ],
        "price_insights": {"lowest_price": 8500, "price_level": "low", "typical_price_range": [8000, 12000]},
    }
    respx.get(SERP).mock(return_value=httpx.Response(200, json=flights))
    out = serpapi_tools.search_flights.invoke(
        {"origin": "CCU", "destination": "DEL", "departure_date": "2026-07-10"}
    )
    assert out["status"] == "ok"
    assert out["cheapest"]["price"] == 8500
    assert out["cheapest"]["booking_token"] == "BT1"
    assert out["cheapest"]["airlines"] == ["IndiGo"]
    assert out["price_insights"]["lowest_price"] == 8500


@respx.mock
def test_resolve_booking_options(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    booking = {
        "booking_options": [
            {"together": {"book_with": "Cleartrip", "price": 8700, "booking_request": {"url": "https://ct/book", "post_data": "x=1"}}},
            {"together": {"book_with": "IndiGo", "price": 8500, "booking_request": {"url": "https://indigo/book"}}},
        ]
    }
    respx.get(SERP).mock(return_value=httpx.Response(200, json=booking))
    out = serpapi_tools.resolve_flight_booking_options.invoke(
        {"booking_token": "BT1", "origin": "CCU", "destination": "DEL", "departure_date": "2026-07-10"}
    )
    assert out["status"] == "ok"
    assert out["cheapest"]["book_with"] == "IndiGo"  # cheapest first
    assert out["cheapest"]["price"] == 8500
    assert out["options"][0]["deep_link"] == "https://indigo/book"


@respx.mock
def test_search_hotels_cheapest_provider(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    hotels = {
        "properties": [
            {
                "name": "Hotel A",
                "overall_rating": 4.2,
                "rate_per_night": {"extracted_lowest": 3500},
                "total_rate": {"extracted_lowest": 7000},
                "prices": [{"source": "Booking.com", "rate_per_night": {"extracted_lowest": 3500}, "link": "http://book", "official": False}],
                "featured_prices": [{"source": "Hotel A Official", "rate_per_night": {"extracted_lowest": 3400}, "link": "http://official", "official": True}],
            }
        ]
    }
    respx.get(SERP).mock(return_value=httpx.Response(200, json=hotels))
    out = serpapi_tools.search_hotels.invoke(
        {"location": "Kolkata", "check_in": "2026-07-10", "check_out": "2026-07-12"}
    )
    cp = out["hotels"][0]["cheapest_provider"]
    assert cp["price_per_night"] == 3400 and cp["official"] is True


@respx.mock
def test_search_products(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    shop = {"shopping_results": [{"title": "Headphones X", "extracted_price": 7999, "price": "₹7,999", "source": "Croma", "link": "http://x", "rating": 4.3, "reviews": 210}]}
    respx.get(SERP).mock(return_value=httpx.Response(200, json=shop))
    out = serpapi_tools.search_products.invoke({"query": "headphones"})
    assert out["count"] == 1
    assert out["currency"] == "INR"  # localized to India, not USD
    p = out["products"][0]
    assert p["price"] == 7999 and p["source"] == "Croma"


def test_price_level_parses_indian_ranges():
    from backend.tools.places_tools import _price_level

    assert _price_level("₹800–1,000") == 2  # midpoint 900
    assert _price_level("₹2,000+") == 3
    assert _price_level("₹200–400") == 1  # midpoint 300
    assert _price_level("$$") == 2  # symbol style still works
    assert _price_level("₹₹₹₹") == 4
    assert _price_level(None) is None


@respx.mock
def test_search_flights_merges_other_flights(monkeypatch):
    """Google often leaves best_flights empty — results must still surface."""
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")
    data = {
        "other_flights": [
            {
                "price": 5445,
                "total_duration": 150,
                "flights": [{"airline": "IndiGo", "departure_airport": {"id": "CCU"}, "arrival_airport": {"id": "DEL"}}],
                "booking_token": "X",
            }
        ],
        "price_insights": {"lowest_price": 5445},
    }
    respx.get(SERP).mock(return_value=httpx.Response(200, json=data))
    out = serpapi_tools.search_flights.invoke({"origin": "CCU", "destination": "DEL", "departure_date": "2026-07-20"})
    assert out["status"] == "ok"
    assert len(out["flights"]) == 1  # merged from other_flights
    assert out["cheapest"]["price"] == 5445


@respx.mock
def test_get_place_photos_resolves_data_id(monkeypatch):
    monkeypatch.setattr(settings, "SERPAPI_API_KEY", "k")

    def handler(request):
        engine = httpx.QueryParams(request.url.query).get("engine")
        if engine == "google_maps":
            return httpx.Response(200, json={"place_results": {"data_id": "DID1"}})
        if engine == "google_maps_photos":
            return httpx.Response(200, json={"photos": [{"image": "http://img1"}, {"image": "http://img2"}]})
        return httpx.Response(200, json={})

    respx.get(SERP).mock(side_effect=handler)
    out = serpapi_tools.get_place_photos.invoke({"place_id": "PID"})
    assert out["status"] == "ok"
    assert out["data_id"] == "DID1"
    assert out["photos"] == ["http://img1", "http://img2"]


def test_web_search(monkeypatch):
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "k")

    class FakeTavily:
        def invoke(self, payload):
            return {"answer": "A", "results": [{"title": "T", "url": "u", "content": "c", "score": 0.9}]}

    monkeypatch.setattr(search_tools, "_get_tavily", lambda: FakeTavily())
    out = search_tools.web_search.invoke({"query": "best dishes kolkata"})
    assert out["status"] == "ok" and out["results"][0]["title"] == "T"


def test_kg_tools(monkeypatch):
    import backend.services.knowledge_graph_service as kgmod

    class FakeKG:
        driver = object()

        def get_user_preferences(self, uid):
            return {"user": {"user_id": uid}, "food_preferences": []}

        def track_restaurant_interaction(self, *a, **k):
            return True

        def get_hybrid_recommendations(self, uid, limit=10):
            return [{"id": "r1", "name": "X", "hybrid_score": 0.8}]

    monkeypatch.setattr(kgmod, "knowledge_graph_service", FakeKG())
    assert kg_tools.get_user_preferences.invoke({"user_id": "u1"})["status"] == "ok"
    assert kg_tools.recommend_restaurants.invoke({"user_id": "u1"})["count"] == 1
    assert kg_tools.track_interaction.invoke(
        {"user_id": "u1", "restaurant_id": "r1", "restaurant_name": "X", "cuisine": "bengali"}
    )["tracked"] is True


def test_search_dishes_graceful_without_index(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    out = rag_tools.search_dishes.invoke({"query": "paneer tikka"})
    assert out["status"] == "ok" and out["count"] == 0
