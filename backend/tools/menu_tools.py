"""Menu tool — structured menu per restaurant (cached; never re-OCRs)."""
from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


@tool
def get_menu(place_id: str, restaurant_name: str = "") -> dict[str, Any]:
    """Get a restaurant's structured menu by `place_id` (cached, never re-OCR'd).

    Runs the menu cascade: cached menu -> user-posted photos -> Gemini classifies
    menu images -> Gemini extracts a structured menu (sections -> items with price,
    description, dietary flags). Pass `restaurant_name` to improve fallback/web
    lookups. Returns {status, restaurant_id, restaurant_name, currency, sections:
    [{name, items:[{id, name, price, description, dietary_flags, ...}]}], source,
    order_online_url}. Use the item `id`s for cart/voice ordering.
    """
    from ..services.menu_service import get_menu as _get_menu

    return _get_menu(place_id, restaurant_name=restaurant_name)
