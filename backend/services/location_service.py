"""
Location helpers — reverse geocoding (lat/lng -> place) and IP geolocation.

Vendor-neutral and key-free: OpenStreetMap Nominatim for reverse geocoding and
ip-api.com for IP fallback. Both wrapped in try/except and degrade gracefully.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx
from loguru import logger

_UA = "Kensho/2.0 (restaurant assistant; contact: dev@kensho.local)"


def _label(addr: dict[str, Any]) -> str:
    """Build a short, human label like 'Park Street, Kolkata'."""
    area = (
        addr.get("suburb")
        or addr.get("neighbourhood")
        or addr.get("road")
        or addr.get("city_district")
    )
    city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state_district") or addr.get("state")
    seen, out = set(), []
    for p in (area, city):
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ", ".join(out)


def reverse_geocode(lat: float, lng: float, timeout: float = 8.0) -> dict[str, Any]:
    """lat/lng -> {status, location, city, state, country, formatted, lat, lng}."""
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "jsonv2", "zoom": 14, "addressdetails": 1},
            headers={"User-Agent": _UA, "Accept-Language": "en"},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        addr = data.get("address", {}) or {}
        return {
            "status": "ok",
            "location": _label(addr) or (data.get("display_name", "").split(",")[0] or None),
            "city": addr.get("city") or addr.get("town") or addr.get("village"),
            "state": addr.get("state"),
            "country": addr.get("country"),
            "formatted": data.get("display_name"),
            "lat": lat,
            "lng": lng,
        }
    except Exception as e:
        logger.warning(f"reverse_geocode failed: {e}")
        return {"status": "error", "message": str(e), "lat": lat, "lng": lng}


def ip_location(ip: Optional[str] = None, timeout: float = 8.0) -> dict[str, Any]:
    """Approximate location from IP (fallback when geolocation is denied)."""
    try:
        r = httpx.get(
            f"http://ip-api.com/json/{ip or ''}",
            params={"fields": "status,message,country,regionName,city,lat,lon,query"},
            timeout=timeout,
        )
        r.raise_for_status()
        d = r.json()
        if d.get("status") != "success":
            return {"status": "error", "message": d.get("message", "ip lookup failed")}
        label = ", ".join(p for p in (d.get("city"), d.get("regionName")) if p)
        return {
            "status": "ok",
            "location": label or d.get("city"),
            "city": d.get("city"),
            "state": d.get("regionName"),
            "country": d.get("country"),
            "lat": d.get("lat"),
            "lng": d.get("lon"),
        }
    except Exception as e:
        logger.warning(f"ip_location failed: {e}")
        return {"status": "error", "message": str(e)}


class LocationService:
    reverse_geocode = staticmethod(reverse_geocode)
    ip_location = staticmethod(ip_location)


location_service = LocationService()
