"""
Per-user routes — the dashboard, activity log, recommendation engine, and taste
graph. Everything is scoped to the authenticated user (the user_id never comes
from the client) and degrades gracefully when a subsystem is unconfigured.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..dependencies import get_current_active_user
from ..services import activity_service, recommend_service
from ..services.user_service import user_service

router = APIRouter(prefix="/me", tags=["me"])


class TrackBody(BaseModel):
    kind: str  # search | view | dish_view | order
    query: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: Optional[str] = None
    cuisine: Optional[str] = None
    domain: str = "restaurant"
    payload: dict[str, Any] = {}


@router.post("/track")
async def track(body: TrackBody, current_user: dict = Depends(get_current_active_user)) -> dict:
    ok = await run_in_threadpool(
        activity_service.record,
        current_user["user_id"],
        body.kind,
        query=body.query,
        restaurant_id=body.restaurant_id,
        restaurant_name=body.restaurant_name,
        cuisine=body.cuisine,
        domain=body.domain,
        payload=body.payload,
    )
    return {"status": "ok" if ok else "skipped"}


@router.get("/activity")
async def activity(
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    items = await run_in_threadpool(activity_service.recent, current_user["user_id"], None, limit)
    return {"status": "ok", "count": len(items), "items": items}


@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(get_current_active_user)) -> dict:
    return await run_in_threadpool(activity_service.dashboard, current_user["user_id"])


@router.get("/recommendations")
async def recommendations(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location: Optional[str] = None,
    limit: int = Query(12, ge=1, le=24),
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    uid = current_user["user_id"]
    restaurants = await run_in_threadpool(
        recommend_service.recommend_restaurants, uid, lat, lng, location, limit
    )
    dishes = await run_in_threadpool(recommend_service.recommend_dishes, uid, limit)
    return {"status": "ok", "restaurants": restaurants, "dishes": dishes}


@router.get("/taste-graph")
async def taste_graph(current_user: dict = Depends(get_current_active_user)) -> dict:
    return await run_in_threadpool(user_service.taste_graph, current_user["user_id"])
