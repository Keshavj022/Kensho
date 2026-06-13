"""Milestone 8 — the full API surface from the spec is registered."""
from __future__ import annotations

from backend.main import app

EXPECTED = {
    "/health", "/health/db", "/health/kg", "/health/rag", "/health/llm",
    "/api/v1/chat",
    "/api/v1/restaurants/search",
    "/api/v1/restaurants/{place_id}",
    "/api/v1/restaurants/{place_id}/menu",
    "/api/v1/restaurants/dishes/search",
    "/api/v1/travel/flights/search",
    "/api/v1/travel/hotels/search",
    "/api/v1/travel/itinerary",
    "/api/v1/shopping/search",
    "/api/v1/voice/stt", "/api/v1/voice/tts", "/api/v1/voice/order", "/api/v1/voice/voices",
    "/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/refresh",
    "/api/v1/auth/logout", "/api/v1/auth/me",
    "/api/v1/knowledge-graph/user/{user_id}/preferences",
}


def test_full_api_surface_registered():
    paths = {r.path for r in app.routes}
    missing = EXPECTED - paths
    assert not missing, f"missing routes: {sorted(missing)}"
