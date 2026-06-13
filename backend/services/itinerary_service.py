"""Synchronous trip planner over the SerpApi/Tavily tools — search-only, no booking.
Each section degrades independently; the day-by-day skeleton is always returned."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from loguru import logger

from ..tools import search_tools, serpapi_tools

ACTIVITIES_PER_DAY = {"relaxed": 2, "moderate": 3, "packed": 4}
_TIME_SLOTS = ["09:00", "13:00", "18:00", "20:30"]
_MEALS = [
    {"type": "breakfast", "time": "08:00", "suggestion": "Hotel breakfast or a local cafe"},
    {"type": "lunch", "time": "12:30", "suggestion": "Local restaurant near the day's activities"},
    {"type": "dinner", "time": "19:30", "suggestion": "Recommended restaurant in the area"},
]


def _parse_date(d: str) -> datetime:
    return datetime.fromisoformat(d[:10])


class ItineraryService:
    """Builds + stores search-derived trip plans (no booking)."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def plan_trip(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        origin: Optional[str] = None,
        travelers: int = 1,
        pace: str = "moderate",
        interests: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Assemble a day-by-day plan from live search data. Returns a dict."""
        try:
            start = _parse_date(start_date)
            end = _parse_date(end_date)
        except Exception:
            return {"status": "error", "message": "Dates must be YYYY-MM-DD"}
        nights = max(0, (end - start).days)
        total_days = max(1, nights if nights > 0 else 1)

        flights: dict[str, Any] = {"status": "skipped", "reason": "no origin provided"}
        if origin:
            flights = serpapi_tools.search_flights.invoke(
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": start_date,
                    "return_date": end_date,
                    "adults": travelers,
                }
            )

        hotels = serpapi_tools.search_hotels.invoke(
            {"location": destination, "check_in": start_date, "check_out": end_date, "guests": travelers}
        )

        interest_str = " ".join(interests) if interests else ""
        act = search_tools.web_search.invoke(
            {"query": f"top attractions and things to do in {destination} {interest_str}".strip()}
        )
        activity_pool = (
            [{"name": r.get("title"), "info": r.get("url"), "summary": (r.get("content") or "")[:160]}
             for r in act.get("results", [])]
            if act.get("status") == "ok"
            else []
        )

        per_day = ACTIVITIES_PER_DAY.get(pace, 3)
        daily = []
        for day_num in range(total_days):
            current = start + timedelta(days=day_num)
            day_acts = []
            if activity_pool:
                for i in range(per_day):
                    act_item = dict(activity_pool[(day_num * per_day + i) % len(activity_pool)])
                    act_item["time"] = _TIME_SLOTS[i] if i < len(_TIME_SLOTS) else None
                    day_acts.append(act_item)
            daily.append(
                {
                    "day": day_num + 1,
                    "date": current.strftime("%Y-%m-%d"),
                    "location": destination,
                    "activities": day_acts,
                    "meals": _MEALS,
                }
            )

        est = 0.0
        currency = "INR"
        if isinstance(flights, dict) and flights.get("cheapest"):
            est += (flights["cheapest"].get("price") or 0) * travelers
            currency = flights.get("currency", currency)
        cheapest_hotel = hotels.get("cheapest") if isinstance(hotels, dict) else None
        if cheapest_hotel and cheapest_hotel.get("price_per_night"):
            est += cheapest_hotel["price_per_night"] * max(1, nights)
            currency = hotels.get("currency", currency)

        plan_id = uuid.uuid4().hex[:8]
        plan = {
            "status": "ok",
            "id": plan_id,
            "trip_name": f"{destination} trip",
            "origin": origin,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "nights": nights,
            "travelers": travelers,
            "pace": pace,
            "flights": flights,
            "hotel": cheapest_hotel,
            "hotels_searched": hotels.get("count") if isinstance(hotels, dict) else 0,
            "daily": daily,
            "estimated_cost": round(est, 2) if est else None,
            "currency": currency,
            "note": "Search-only planner — surface deep links/price context; no booking.",
        }
        self._store[plan_id] = plan
        logger.info(f"Planned trip {plan_id}: {destination} ({total_days} day(s))")
        return plan

    def get_itinerary(self, plan_id: str) -> Optional[dict[str, Any]]:
        return self._store.get(plan_id)


itinerary_service = ItineraryService()
