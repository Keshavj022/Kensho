"""Restaurant domain routes (direct tool-backed; the menu route is added in M5)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..tools import places_tools, rag_tools

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


class RestaurantSearchBody(BaseModel):
    query: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    cuisine: Optional[str] = None
    price_level: Optional[int] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None
    dietary: Optional[str] = None
    radius: int = 5000
    max_results: int = 20


class DishSearchBody(BaseModel):
    query: str
    max_results: int = 10
    restaurant_id: Optional[str] = None


@router.post("/search")
async def search_restaurants(body: RestaurantSearchBody) -> dict:
    return await run_in_threadpool(places_tools.search_restaurants.invoke, body.model_dump())


@router.post("/dishes/search")
async def search_dishes(body: DishSearchBody) -> dict:
    return await run_in_threadpool(rag_tools.search_dishes.invoke, body.model_dump())


@router.get("/{place_id}")
async def restaurant_details(place_id: str) -> dict:
    return await run_in_threadpool(places_tools.get_restaurant_details.invoke, {"place_id": place_id})
