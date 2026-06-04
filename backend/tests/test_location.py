"""Location helpers — reverse geocode parsing (Nominatim mocked) + route wiring."""
from __future__ import annotations

import httpx
import respx

from backend.services.location_service import reverse_geocode

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"


@respx.mock
def test_reverse_geocode_parses_label():
    respx.get(NOMINATIM).mock(
        return_value=httpx.Response(
            200,
            json={
                "display_name": "Park Street, Kolkata, West Bengal, India",
                "address": {"suburb": "Park Street", "city": "Kolkata", "state": "West Bengal", "country": "India"},
            },
        )
    )
    r = reverse_geocode(22.55, 88.35)
    assert r["status"] == "ok"
    assert r["city"] == "Kolkata"
    assert "Park Street" in r["location"] and "Kolkata" in r["location"]
    assert r["lat"] == 22.55 and r["lng"] == 88.35


@respx.mock
def test_reverse_geocode_graceful_on_failure():
    respx.get(NOMINATIM).mock(return_value=httpx.Response(503))
    r = reverse_geocode(0, 0)
    assert r["status"] == "error"


def test_location_routes_registered():
    from backend.main import app

    paths = {r.path for r in app.routes}
    assert "/api/v1/location/reverse" in paths
    assert "/api/v1/location/ip" in paths
    assert "/api/v1/location/nearest-airport" in paths


def test_nearest_airport():
    from backend.services.airports import airport_for_city, home_airport, nearest_airport

    assert nearest_airport(22.57, 88.36)["iata"] == "CCU"  # Kolkata
    assert nearest_airport(15.4, 73.9)["iata"] == "GOI"  # Goa
    assert airport_for_city("Park Street, Kolkata")["iata"] == "CCU"
    assert home_airport(28.61, 77.20)["iata"] == "DEL"  # Delhi
    assert home_airport(None, None, "nowhere-ville") is None


def test_nearest_airport_route(client):
    r = client.get("/api/v1/location/nearest-airport", params={"lat": 22.57, "lng": 88.36})
    assert r.status_code == 200 and r.json()["iata"] == "CCU"
