"""Travel domain routes — flight/hotel metasearch + trip itinerary (no booking)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..tools import serpapi_tools, trip_tools

router = APIRouter(prefix="/travel", tags=["travel"])


class FlightSearchBody(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = 1
    sort: str = "price"


class HotelSearchBody(BaseModel):
    location: str
    check_in: str
    check_out: str
    guests: int = 1


class TripPlanBody(BaseModel):
    destination: str
    start_date: str
    end_date: str
    origin: Optional[str] = None
    travelers: int = 1
    pace: str = "moderate"
    interests: Optional[list[str]] = None


@router.post("/flights/search")
async def search_flights(body: FlightSearchBody) -> dict:
    return await run_in_threadpool(serpapi_tools.search_flights.invoke, body.model_dump())


@router.post("/hotels/search")
async def search_hotels(body: HotelSearchBody) -> dict:
    return await run_in_threadpool(serpapi_tools.search_hotels.invoke, body.model_dump())


@router.post("/itinerary")
async def plan_itinerary(body: TripPlanBody) -> dict:
    return await run_in_threadpool(trip_tools.plan_trip.invoke, body.model_dump())
