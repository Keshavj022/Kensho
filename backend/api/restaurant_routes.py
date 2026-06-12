"""Restaurant domain routes — search, featured (highly-rated), dish search/featured,
menu prefetch (background), photos, and details."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..tools import places_tools, rag_tools, serpapi_tools

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


class PrefetchItem(BaseModel):
    place_id: str
    name: str = ""


class PrefetchBody(BaseModel):
    items: list[PrefetchItem] = []
    cap: int = 8


@router.post("/search")
async def search_restaurants(body: RestaurantSearchBody) -> dict:
    return await run_in_threadpool(places_tools.search_restaurants.invoke, body.model_dump())


@router.get("/featured")
async def featured_restaurants(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location: Optional[str] = None,
    dietary: Optional[str] = None,
    limit: int = Query(12, ge=1, le=24),
) -> dict:
    """Highly-rated restaurants near a point — the Eat page's default view."""
    from ..services import recommend_service

    return await run_in_threadpool(
        recommend_service.featured_restaurants, lat, lng, location, dietary, limit
    )


@router.post("/dishes/search")
async def search_dishes(body: DishSearchBody) -> dict:
    return await run_in_threadpool(rag_tools.search_dishes.invoke, body.model_dump())


@router.get("/dishes/featured")
async def featured_dishes(limit: int = Query(12, ge=1, le=24)) -> dict:
    """Highly-rated / signature dishes from menus Kensho has already read."""
    from ..services import recommend_service

    return await run_in_threadpool(recommend_service.featured_dishes, limit)


@router.post("/menu/prefetch")
async def prefetch_menus(body: PrefetchBody, background: BackgroundTasks) -> dict:
    """Kick off background menu extraction for a batch of places (cached ones skipped).

    Returns immediately; the 'Find a dish' view fills in as menus land.
    """
    from ..services.menu_service import prefetch_menus as _prefetch

    items = [i.model_dump() for i in body.items]
    background.add_task(_prefetch, items, body.cap)
    return {"status": "scheduled", "queued": min(len(items), body.cap)}


@router.get("/{place_id}/photos")
async def restaurant_photos(place_id: str, limit: int = Query(12, ge=1, le=30)) -> dict:
    """User-posted photo URLs for a place (gallery display)."""
    res = await run_in_threadpool(serpapi_tools.get_place_photos.invoke, {"place_id": place_id})
    if isinstance(res, dict) and res.get("photos"):
        res = {**res, "photos": res["photos"][: int(limit)]}
    return res


@router.get("/{place_id}")
async def restaurant_details(place_id: str) -> dict:
    return await run_in_threadpool(places_tools.get_restaurant_details.invoke, {"place_id": place_id})
