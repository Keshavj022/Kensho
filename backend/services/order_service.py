"""Voice ordering: resolve a transcript to real menu item_ids, build a cart, and hand
off to the order_online link. Matching only ever maps to existing items, never invents."""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Optional

from loguru import logger

from ..db.database import session_scope
from ..db.models import Cart
from .llm import invoke_with_fallback, is_llm_available
from .ocr_service import _parse_json


def _menu_items(place_id: str) -> tuple[list[dict], Optional[str], str]:
    from .menu_service import get_menu

    menu = get_menu(place_id)
    items: list[dict] = []
    for section in menu.get("sections", []):
        for it in section.get("items", []):
            items.append({"id": it["id"], "name": it["name"], "price": it.get("price"), "section": it.get("section")})
    return items, menu.get("order_online_url"), menu.get("restaurant_name") or place_id


def _resolve_with_llm(transcript: str, items: list[dict]) -> list[dict]:
    listing = "\n".join(f'{i["id"]}: {i["name"]}' for i in items)
    prompt = (
        f"A restaurant's menu items (id: name):\n{listing}\n\n"
        f'The customer said: "{transcript}"\n\n'
        "Return ONLY JSON: a list of {\"item_id\": <one id from the list above>, "
        '"qty": <integer>} for the items they want to order. Use ONLY item_ids that '
        "appear in the list — never invent one. If nothing matches, return []."
    )
    resp = invoke_with_fallback(prompt, temperature=0)
    data = _parse_json(getattr(resp, "content", "") or "") or []
    valid = {i["id"] for i in items}
    out = []
    for d in data if isinstance(data, list) else []:
        if isinstance(d, dict) and d.get("item_id") in valid:
            out.append({"item_id": d["item_id"], "qty": max(1, int(d.get("qty", 1) or 1))})
    return out


def _resolve_with_fuzzy(transcript: str, items: list[dict], threshold: float = 0.72) -> list[dict]:
    t = transcript.lower()
    out = []
    for it in items:
        name = it["name"].lower()
        words = name.split()
        if name in t or (len(words) > 1 and all(w in t for w in words)):
            out.append({"item_id": it["id"], "qty": 1})
            continue
        best = max((SequenceMatcher(None, name, w).ratio() for w in t.split()), default=0.0)
        if best >= threshold:
            out.append({"item_id": it["id"], "qty": 1})
    return out


def resolve_order(transcript: str, items: list[dict]) -> list[dict]:
    """Map a transcript to [{item_id, qty}] using ONLY existing item_ids."""
    if not transcript or not items:
        return []
    if is_llm_available():
        try:
            return _resolve_with_llm(transcript, items)
        except Exception as e:
            logger.warning(f"LLM order resolution failed, falling back to fuzzy: {e}")
    return _resolve_with_fuzzy(transcript, items)


def _update_cart(owner_key: str, place_id: str, restaurant_name: str, resolved: list[dict],
                 items_by_id: dict[str, dict], order_url: Optional[str]) -> dict:
    with session_scope() as db:
        cart = db.query(Cart).filter_by(owner_key=owner_key, restaurant_id=place_id).first()
        if cart is None:
            cart = Cart(owner_key=owner_key, restaurant_id=place_id, restaurant_name=restaurant_name, items=[])
            db.add(cart)
        current = {i["item_id"]: dict(i) for i in (cart.items or [])}
        for r in resolved:
            it = items_by_id[r["item_id"]]
            if r["item_id"] in current:
                current[r["item_id"]]["qty"] += r["qty"]
            else:
                current[r["item_id"]] = {"item_id": r["item_id"], "name": it["name"], "price": it["price"], "qty": r["qty"]}
        cart.items = list(current.values())
        cart.restaurant_name = restaurant_name
        cart.order_online_url = order_url
        snapshot = {
            "owner_key": owner_key,
            "restaurant_id": place_id,
            "restaurant_name": restaurant_name,
            "items": cart.items,
            "order_online_url": order_url,
            "total": round(sum((i.get("price") or 0) * i["qty"] for i in cart.items), 2),
        }
    return snapshot


def process_voice_order(
    audio: Optional[bytes],
    text: Optional[str],
    place_id: str,
    owner_key: str = "anon",
    language: Optional[str] = None,
) -> dict[str, Any]:
    """audio -> STT -> resolve to menu item_ids -> cart -> order_online handoff."""
    transcript = text or ""
    provider = None
    if audio:
        from .voice_service import voice_service

        stt = voice_service.transcribe(audio, language=language)
        if stt["status"] != "ok":
            return {"status": stt["status"], "message": stt.get("message"), "transcript": ""}
        transcript = stt["text"]
        provider = stt.get("provider")
    if not transcript:
        return {"status": "error", "message": "No transcript or text provided", "transcript": ""}

    items, order_url, rname = _menu_items(place_id)
    if not items:
        return {
            "status": "no_menu",
            "message": "No menu available for this restaurant yet.",
            "transcript": transcript,
            "order_online_url": order_url,
        }

    resolved = resolve_order(transcript, items)
    items_by_id = {i["id"]: i for i in items}
    cart = _update_cart(owner_key, place_id, rname, resolved, items_by_id, order_url)

    matched = [{"item_id": r["item_id"], "name": items_by_id[r["item_id"]]["name"], "qty": r["qty"]} for r in resolved]
    if matched:
        names = ", ".join(f'{m["qty"]}x {m["name"]}' for m in matched)
        confirmation = f"Added {names} to your cart. Cart total is {cart['total']}."
    else:
        confirmation = "Sorry, I couldn't match anything on the menu to your request. Could you try again?"

    return {
        "status": "ok",
        "transcript": transcript,
        "stt_provider": provider,
        "matched": matched,
        "cart": cart,
        "order_online_url": order_url,
        "confirmation_text": confirmation,
    }


def get_cart(owner_key: str, place_id: str) -> dict:
    with session_scope() as db:
        cart = db.query(Cart).filter_by(owner_key=owner_key, restaurant_id=place_id).first()
        if cart is None:
            return {"status": "empty", "items": [], "total": 0}
        items = cart.items or []
        return {
            "status": "ok",
            "restaurant_id": place_id,
            "restaurant_name": cart.restaurant_name,
            "items": items,
            "order_online_url": cart.order_online_url,
            "total": round(sum((i.get("price") or 0) * i["qty"] for i in items), 2),
        }
