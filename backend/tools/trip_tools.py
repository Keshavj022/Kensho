"""
Trip planning tool — assembles a day-by-day itinerary (search-only, no booking).
"""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool


@tool
def plan_trip(
    destination: str,
    start_date: str,
    end_date: str,
    origin: Optional[str] = None,
    travelers: int = 1,
    pace: str = "moderate",
    interests: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Plan a day-by-day trip itinerary for a destination (search-only, no booking).

    `start_date`/`end_date` are YYYY-MM-DD. Optional `origin` (IATA/city code) adds
    a flight metasearch; `pace` is relaxed/moderate/packed (2/3/4 activities per
    day); `interests` is a list like ["food","history","nature"]. Returns a plan
    with {flights (cheapest + price context), hotel (cheapest provider), daily:[{day,
    date, activities, meals}], estimated_cost}. Surfaces deep links/prices only —
    never books or takes payment.
    """
    from ..services.itinerary_service import itinerary_service

    return itinerary_service.plan_trip(
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        origin=origin,
        travelers=travelers,
        pace=pace,
        interests=interests,
    )
