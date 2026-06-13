"""Location utilities — reverse geocoding + IP fallback (public, key-free)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.concurrency import run_in_threadpool

from ..services.airports import home_airport
from ..services.location_service import location_service

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/nearest-airport")
async def nearest_airport(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    city: Optional[str] = Query(None),
) -> dict:
    """Nearest airport from coordinates, or matched from a city name."""
    return home_airport(lat, lng, city) or {"status": "not_found"}


@router.get("/reverse")
async def reverse(lat: float = Query(...), lng: float = Query(...)) -> dict:
    return await run_in_threadpool(location_service.reverse_geocode, lat, lng)


@router.get("/ip")
async def ip(request: Request) -> dict:
    client = request.client.host if request.client else None
    if not client or client in ("127.0.0.1", "::1", "testclient") or client.startswith(("10.", "192.168.", "172.")):
        client = None
    return await run_in_threadpool(location_service.ip_location, client)
