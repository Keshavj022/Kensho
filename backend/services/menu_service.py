"""Menu pipeline: cache check → photos → classify → OCR extract → persist + embed.
A place is read at most once; the outcome (success or failure) is cached."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from loguru import logger

from ..config import settings
from ..db.database import session_scope
from ..db.models import MenuCache
from ..models.menu import Menu
from . import ocr_service
from .vector_index import add_menu_items


def _resolve_order_link(place_id: str) -> Optional[str]:
    """Best-effort Google 'order online' deep link via SerpApi google_maps."""
    from ..tools import _serpapi

    data = _serpapi.serpapi_search({"engine": "google_maps", "place_id": place_id})
    if data.get("_error"):
        return None
    pr = data.get("place_results") or {}
    order = pr.get("order_online")
    if isinstance(order, dict) and order.get("link"):
        return order["link"]
    if isinstance(order, list) and order and isinstance(order[0], dict):
        return order[0].get("link")
    return None


def _get_cached(place_id: str) -> Optional[dict[str, Any]]:
    ttl = timedelta(days=settings.MENU_CACHE_TTL_DAYS)
    with session_scope() as db:
        row = db.get(MenuCache, place_id)
        if not row:
            return None
        if datetime.utcnow() - row.extracted_at > ttl:
            return None
        menu = dict(row.menu_json)
        menu["status"] = "ok"
        menu["cached"] = True
        return menu


def _persist(menu: Menu) -> None:
    payload = menu.model_dump(mode="json")
    with session_scope() as db:
        row = db.get(MenuCache, menu.restaurant_id)
        if row is None:
            row = MenuCache(place_id=menu.restaurant_id)
            db.add(row)
        row.restaurant_name = menu.restaurant_name
        row.menu_json = payload
        row.source = menu.source
        row.order_online_url = menu.order_online_url
        row.extracted_at = datetime.utcnow()
    items = [i.model_dump() for i in menu.all_items()]
    if items:
        add_menu_items(menu.restaurant_id, menu.restaurant_name, items)


def _result(menu: Menu, cached: bool = False) -> dict[str, Any]:
    out = menu.model_dump(mode="json")
    out["status"] = "ok"
    out["cached"] = cached
    return out


def get_menu(place_id: str, restaurant_name: str = "", force: bool = False) -> dict[str, Any]:
    """Run the menu cascade for a place_id. Returns the structured menu dict.

    FETCH-ONCE guarantee: a restaurant is read at most once. The cache short-circuits
    every subsequent open, and the OUTCOME is cached whether the read succeeded, found
    no menu, or the pipeline crashed — so a broken place is never re-fetched on every
    open. The one exception is "OCR not configured" (missing keys): that isn't cached,
    so it retries cheaply (fail-fast, no slow OCR) once you set the keys up. Pass
    force=True (the menu route's ?refresh=true) to re-scan on demand.
    """
    if not force:
        cached = _get_cached(place_id)
        if cached is not None:
            return cached

    try:
        return _fetch_and_cache(place_id, restaurant_name)
    except Exception as e:
        logger.warning(f"menu pipeline failed for {place_id}: {e}")
        order_url = None
        try:
            order_url = _resolve_order_link(place_id)
        except Exception:
            pass
        menu = Menu(
            restaurant_id=place_id,
            restaurant_name=restaurant_name or place_id,
            sections=[],
            source="web",
            order_online_url=order_url,
        )
        try:
            _persist(menu)
        except Exception as pe:  # pragma: no cover - defensive
            logger.warning(f"negative-cache persist failed for {place_id}: {pe}")
        out = _result(menu)
        out["note"] = "We couldn't read a menu for this place — showing the order link only."
        return out


def _fetch_and_cache(place_id: str, restaurant_name: str) -> dict[str, Any]:
    """The actual cascade (photos -> classify -> extract -> persist). Wrapped by
    get_menu so any throw becomes a cached negative."""
    from ..tools import search_tools, serpapi_tools

    photos_res = serpapi_tools.get_place_photos.invoke({"place_id": place_id})
    photo_urls = photos_res.get("photos", []) if isinstance(photos_res, dict) else []
    order_url = _resolve_order_link(place_id)

    menu: Optional[Menu] = None
    if photo_urls and ocr_service.is_llm_available():
        menu_photos = ocr_service.classify_menu_images(photo_urls)
        if menu_photos:
            menu = ocr_service.extract_menu(place_id, restaurant_name or place_id, menu_photos)
            if menu is not None:
                menu.raw_photo_urls = photo_urls[:20]
                menu.order_online_url = order_url

    if menu is None:
        configured = settings.serpapi_configured and ocr_service.is_llm_available()
        web_note = None
        if settings.tavily_configured and restaurant_name:
            web = search_tools.web_search.invoke({"query": f"{restaurant_name} menu prices"})
            if web.get("status") == "ok" and web.get("results"):
                web_note = web["results"][0].get("url")
        menu = Menu(
            restaurant_id=place_id,
            restaurant_name=restaurant_name or place_id,
            sections=[],
            source="web",
            raw_photo_urls=photo_urls[:20],
            order_online_url=order_url or web_note,
        )
        if configured:
            _persist(menu)
            out = _result(menu)
            out["note"] = "No readable menu photos found; showing the order link only."
            return out
        out = _result(menu)
        out["status"] = "not_configured"
        out["note"] = "Menu reading isn't configured yet (needs SERPAPI_API_KEY + a vision LLM like Azure OpenAI or Gemini)."
        return out

    _persist(menu)
    return _result(menu)


def is_cached(place_id: str) -> bool:
    """True if a fresh menu is already cached (skip background re-work)."""
    return _get_cached(place_id) is not None


def prefetch_menus(items: list[dict[str, Any]], cap: int = 8) -> dict[str, Any]:
    """Best-effort background extraction for a batch of restaurants.

    `items` = [{place_id, name}]. Skips any place whose menu is already cached.
    Designed to run in a FastAPI BackgroundTask after the Eat page loads, so the
    'Find a dish' view fills in and dish search lights up — never raises.
    """
    done, skipped, failed = 0, 0, 0
    for it in items[: max(0, int(cap))]:
        pid = (it or {}).get("place_id")
        if not pid:
            continue
        try:
            if is_cached(pid):
                skipped += 1
                continue
            get_menu(pid, (it.get("name") or ""))
            done += 1
        except Exception as e:  # pragma: no cover - background best-effort
            failed += 1
            logger.debug(f"prefetch_menus failed for {pid}: {e}")
    logger.info(f"menu prefetch: extracted={done} cached={skipped} failed={failed}")
    return {"extracted": done, "cached": skipped, "failed": failed}
