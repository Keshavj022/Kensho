"""Vision OCR for the menu pipeline: classify which photos are menus, then read
them into a structured Menu. Multilingual; escalates to a stronger model on hard
photos; returns []/None when no vision LLM is available."""
from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from ..models.menu import Menu, MenuItem, make_item_id
from .llm import invoke_with_fallback, is_llm_available

_MAX_CLASSIFY_IMAGES = 12
_MAX_EXTRACT_IMAGES = 6


class _ExtractedItem(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    section: Optional[str] = None
    dietary_flags: list[str] = Field(default_factory=list)
    spice_level: Optional[str] = None
    confidence: float = 0.8


def _download_image(url: str, timeout: float = 15.0) -> Optional[tuple[str, str]]:
    """Download an image -> (base64, mime_type), or None on failure."""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        mime = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        if not mime.startswith("image/"):
            mime = "image/jpeg"
        return base64.b64encode(resp.content).decode("utf-8"), mime
    except Exception as e:
        logger.debug(f"image download failed ({url[:60]}): {e}")
        return None


def _image_block(b64: str, mime: str) -> dict[str, Any]:
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def _parse_json(text: str) -> Optional[Any]:
    """Extract a JSON object/array from an LLM response (tolerates code fences/prose)."""
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def _classify_with_azure_vision(photo_urls: list[str], max_images: int) -> Optional[list[str]]:
    """Deterministic menu classification via Azure Vision OCR density. Returns the
    menu subset, or None when Azure Vision is unavailable (so the caller falls back
    to the multimodal LLM classifier)."""
    from .azure_vision_service import azure_vision_service

    if not azure_vision_service.available:
        return None
    kept = [u for u in photo_urls[:max_images] if azure_vision_service.looks_like_menu(u)]
    logger.info(f"Menu classification (Azure Vision): {len(kept)}/{min(len(photo_urls), max_images)} are menus")
    return kept


def classify_menu_images(photo_urls: list[str], max_images: int = _MAX_CLASSIFY_IMAGES) -> list[str]:
    """Return the subset of photo_urls that are photos of a printed/written MENU.

    User-posted photos aren't labeled. Azure Vision (OCR density) classifies them
    when configured; otherwise a multimodal LLM (Azure OpenAI / Gemini) decides.
    Returns [] when no vision/LLM provider is available.
    """
    if not photo_urls:
        return []

    azure_result = _classify_with_azure_vision(photo_urls, max_images)
    if azure_result:
        return azure_result

    if not is_llm_available():
        return []
    from langchain_core.messages import HumanMessage

    blocks, kept = [], []
    for url in photo_urls[:max_images]:
        dl = _download_image(url)
        if dl:
            blocks.append(_image_block(*dl))
            kept.append(url)
    if not blocks:
        return []

    prompt = (
        f"You are shown {len(kept)} images (0-indexed in order). Identify which images "
        "are photographs of a restaurant MENU — i.e. a printed or handwritten list of food/"
        "drink items, typically with prices. EXCLUDE photos of plated dishes, interiors, "
        "storefronts, people, or receipts. Respond with ONLY JSON: "
        '{"menu_indices": [list of 0-based integer indices that are menus]}'
    )
    try:
        msg = HumanMessage(content=[{"type": "text", "text": prompt}, *blocks])
        resp = invoke_with_fallback([msg], vision=True, temperature=0)
        data = _parse_json(getattr(resp, "content", "") or "")
        indices = (data or {}).get("menu_indices", []) if isinstance(data, dict) else []
        result = [kept[i] for i in indices if isinstance(i, int) and 0 <= i < len(kept)]
        logger.info(f"Menu classification: {len(result)}/{len(kept)} photos are menus")
        return result
    except Exception as e:
        logger.warning(f"classify_menu_images failed: {e}")
        return []


_EXTRACT_PROMPT = (
    "You are an expert menu transcriber. Read EVERY food and drink item from the menu "
    "image(s) and return ONLY JSON (no prose, no code fences) matching exactly:\n"
    '{"currency": "INR", "items": [{"name": str, "description": str|null, '
    '"price": number|null, "section": str|null, "dietary_flags": [str], '
    '"spice_level": str|null, "confidence": number 0..1}]}\n'
    "Rules: preserve item names as printed (may be Hindi/Bengali/other scripts); "
    "section is the menu heading the item sits under (e.g. 'Starters', 'Biryani'); "
    "dietary_flags from {veg, non_veg, vegan, egg, contains_nuts, jain, halal} when "
    "evident; price is the number only (no currency symbol); confidence reflects how "
    "clearly you could read the item. Include every legible item."
)


def _build_menu(restaurant_id: str, restaurant_name: str, extracted: list[_ExtractedItem],
                currency: str, source: str, raw_photo_urls: list[str]) -> Menu:
    sections: dict[str, list[dict]] = {}
    order: list[str] = []
    for it in extracted:
        section = (it.section or "Menu").strip() or "Menu"
        if section not in sections:
            sections[section] = []
            order.append(section)
        item = MenuItem(
            id=make_item_id(restaurant_id, section, it.name),
            name=it.name,
            description=it.description,
            price=it.price,
            currency=currency,
            section=section,
            dietary_flags=it.dietary_flags,
            spice_level=it.spice_level,
            source="ocr",
            confidence=it.confidence,
        )
        sections[section].append(item.model_dump())
    return Menu(
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name,
        currency=currency,
        sections=[{"name": s, "items": sections[s]} for s in order],
        source=source,  # "ocr"
        raw_photo_urls=raw_photo_urls,
    )


def extract_menu(
    restaurant_id: str,
    restaurant_name: str,
    image_urls: list[str],
    use_pro: bool = False,
) -> Optional[Menu]:
    """Read menu photo(s) into a structured Menu (source='ocr'), or None if degraded.

    Escalates to the Pro model once when Flash yields no items.
    """
    if not is_llm_available() or not image_urls:
        return None
    from langchain_core.messages import HumanMessage

    blocks = []
    used_urls = []
    for url in image_urls[:_MAX_EXTRACT_IMAGES]:
        dl = _download_image(url)
        if dl:
            blocks.append(_image_block(*dl))
            used_urls.append(url)
    if not blocks:
        return None

    try:
        msg = HumanMessage(content=[{"type": "text", "text": _EXTRACT_PROMPT}, *blocks])
        resp = invoke_with_fallback([msg], vision=True, temperature=0, use_pro=use_pro)
        data = _parse_json(getattr(resp, "content", "") or "")
        if not isinstance(data, dict):
            data = {"items": data} if isinstance(data, list) else {}
        currency = (data.get("currency") or "INR").strip() or "INR"
        items = []
        for raw in data.get("items", []):
            try:
                items.append(_ExtractedItem(**raw))
            except Exception:
                continue
        if not items and not use_pro:
            logger.info(f"Flash extraction empty for {restaurant_id}; escalating to Pro")
            return extract_menu(restaurant_id, restaurant_name, image_urls, use_pro=True)
        if not items:
            return None
        menu = _build_menu(restaurant_id, restaurant_name, items, currency, "ocr", used_urls)
        logger.info(
            f"Extracted {menu.item_count()} items in {len(menu.sections)} sections "
            f"for {restaurant_name} ({'Pro' if use_pro else 'Flash'})"
        )
        return menu
    except Exception as e:
        logger.warning(f"extract_menu failed for {restaurant_id}: {e}")
        if not use_pro:
            return extract_menu(restaurant_id, restaurant_name, image_urls, use_pro=True)
        return None
