"""Menu route — structured menu + photo URLs for the website."""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/restaurants", tags=["menu"])


@router.get("/{place_id}/menu")
async def get_restaurant_menu(
    place_id: str,
    restaurant_name: str = Query("", description="Improves fallback/web lookup"),
    refresh: bool = Query(False, description="Force re-extraction, bypassing the cache"),
) -> dict:
    from ..services.menu_service import get_menu

    return await run_in_threadpool(get_menu, place_id, restaurant_name, refresh)
