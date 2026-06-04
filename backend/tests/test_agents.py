"""Milestone 4 — specialists + supervisor routing + per-domain routes."""
from __future__ import annotations

import backend.agents.supervisor as sup
import backend.services.llm as llm
from backend.config import settings


def test_domain_routes_degrade_gracefully(client):
    assert client.post("/api/v1/restaurants/search", json={"query": "ramen", "location": "Kolkata"}).json()["status"] == "not_configured"
    assert client.post("/api/v1/travel/flights/search", json={"origin": "CCU", "destination": "DEL", "departure_date": "2026-07-10"}).json()["status"] == "not_configured"
    assert client.post("/api/v1/travel/hotels/search", json={"location": "Kolkata", "check_in": "2026-07-10", "check_out": "2026-07-12"}).json()["status"] == "not_configured"
    assert client.post("/api/v1/shopping/search", json={"query": "headphones"}).json()["status"] == "not_configured"


def test_itinerary_returns_skeleton_without_keys(client):
    body = {"destination": "Kolkata", "start_date": "2026-07-10", "end_date": "2026-07-13"}
    r = client.post("/api/v1/travel/itinerary", json=body).json()
    assert r["status"] == "ok"
    assert len(r["daily"]) == 3
    assert r["daily"][0]["day"] == 1 and "meals" in r["daily"][0]


def test_content_to_text_flattens_gemini_blocks():
    from backend.agents.supervisor import _content_to_text

    assert _content_to_text("hello") == "hello"
    blocks = [
        {"type": "text", "text": "line1", "extras": {"signature": "noise"}},
        {"type": "text", "text": "line2"},
    ]
    assert _content_to_text(blocks) == "line1\nline2"
    assert _content_to_text([]) == ""
    assert _content_to_text(None) == ""


def test_supervisor_wires_three_specialists():
    original = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "AIza-dummy-build-check"
    try:
        llm.reset_llm_caches()
        sup.reset_supervisor()
        graph = sup.get_supervisor()
        nodes = set(graph.get_graph().nodes)
        assert {"supervisor", "restaurant_agent", "travel_agent", "shopping_agent"} <= nodes
    finally:
        settings.GEMINI_API_KEY = original
        llm.reset_llm_caches()
        sup.reset_supervisor()
