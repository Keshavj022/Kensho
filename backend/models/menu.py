"""Menu schema (Pydantic v2). The MenuCache ORM row stores Menu.model_dump()."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

Source = Literal["structured", "ocr", "web"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def make_item_id(restaurant_id: str, section: str | None, name: str) -> str:
    """Deterministic, stable item id so voice ordering can map to a real id."""
    raw = f"{restaurant_id}|{(section or '').lower()}|{name.lower().strip()}"
    return "item_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


class MenuItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "INR"
    section: Optional[str] = None
    dietary_flags: list[str] = Field(default_factory=list)  # e.g. ["veg","vegan","contains_nuts"]
    spice_level: Optional[str] = None
    image_url: Optional[str] = None
    source: Source = "ocr"
    confidence: float = 1.0


class MenuSection(BaseModel):
    name: str
    items: list[MenuItem] = Field(default_factory=list)


class Menu(BaseModel):
    restaurant_id: str  # = place_id
    restaurant_name: str
    currency: str = "INR"
    sections: list[dict] = Field(default_factory=list)  # [{ "name": str, "items": [MenuItem...] }]
    source: Source = "ocr"
    extracted_at: datetime = Field(default_factory=_now)
    raw_photo_urls: list[str] = Field(default_factory=list)
    order_online_url: Optional[str] = None  # food.google.com/chooseprovider link

    def all_items(self) -> list[MenuItem]:
        """Flatten every section's items into one list of MenuItem."""
        out: list[MenuItem] = []
        for section in self.sections:
            for raw in section.get("items", []):
                out.append(raw if isinstance(raw, MenuItem) else MenuItem(**raw))
        return out

    def item_count(self) -> int:
        return sum(len(s.get("items", [])) for s in self.sections)

    @classmethod
    def from_sections(
        cls,
        restaurant_id: str,
        restaurant_name: str,
        sections: list[MenuSection],
        *,
        source: Source = "ocr",
        currency: str = "INR",
        raw_photo_urls: list[str] | None = None,
        order_online_url: str | None = None,
    ) -> "Menu":
        """Build a Menu from typed sections, serializing items to dicts."""
        return cls(
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name,
            currency=currency,
            sections=[
                {"name": s.name, "items": [i.model_dump() for i in s.items]} for s in sections
            ],
            source=source,
            raw_photo_urls=raw_photo_urls or [],
            order_online_url=order_online_url,
        )
