"""Diet filtering for menu items. Combines the OCR dietary_flags with a keyword
classifier over the item name (flags are often missing) and excludes anything that
violates the diner's diet. Errs toward excluding when a non-veg signal is present."""
from __future__ import annotations

import re
from typing import Iterable, Optional

_MEAT = [
    "chicken", "mutton", "lamb", "beef", "pork", "bacon", "sausage", "salami", "pepperoni",
    "keema", "kheema", "qeema", "gosht", "murgh", "duck", "turkey", "veal", "venison",
    "mangsho", "mangsha", "goat", "meat", "ham", "drumstick", "tangdi", "tangri", "kosha",
]
_SEAFOOD = [
    "fish", "prawn", "shrimp", "crab", "lobster", "squid", "calamari", "oyster", "mussel",
    "machli", "macher", "maach", "chingri", "pomfret", "hilsa", "ilish", "bhetki", "rohu",
    "tuna", "salmon", "anchovy", "clam", "tilapia", "basa", "surmai", "scampi", "prawns",
]
_EGG = ["egg", "eggs", "omelette", "omelet", "anda"]
_DAIRY = [
    "paneer", "cheese", "butter", "ghee", "cream", "curd", "dahi", "yogurt", "yoghurt",
    "khoya", "malai", "kheer", "lassi", "makhani", "mawa", "milk", "chenna", "custard",
]
_PORK = ["pork", "bacon", "ham", "pepperoni", "lard", "sausage", "salami"]


def _compile(words: list[str]) -> re.Pattern:
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b")


_RE = {
    "meat": _compile(_MEAT),
    "seafood": _compile(_SEAFOOD),
    "egg": _compile(_EGG),
    "dairy": _compile(_DAIRY),
    "pork": _compile(_PORK),
}


def detect_tags(name: str, flags: Optional[Iterable[str]] = None) -> set[str]:
    text = (name or "").lower()
    flagset = {str(f).lower().replace("-", "_") for f in (flags or [])}
    tags: set[str] = set()
    for tag, pattern in _RE.items():
        if pattern.search(text):
            tags.add(tag)
    if flagset & {"non_veg", "nonveg", "meat"}:
        tags.add("meat")
    if flagset & {"egg", "contains_egg"}:
        tags.add("egg")
    if flagset & {"seafood", "fish"}:
        tags.add("seafood")
    if flagset & {"dairy", "contains_dairy"}:
        tags.add("dairy")
    return tags


def diet_allows(dietary_type: Optional[str], name: str, flags: Optional[Iterable[str]] = None) -> bool:
    """True if an item is allowed for the given diet. Non-vegetarian allows everything."""
    dt = (dietary_type or "non-vegetarian").strip().lower().replace(" ", "-").replace("_", "-")
    if dt in ("", "none", "non-vegetarian", "nonveg"):
        return True
    tags = detect_tags(name, flags)
    if dt == "pescatarian":
        return not (tags & {"meat", "pork"})
    if dt == "vegan":
        return not (tags & {"meat", "seafood", "pork", "egg", "dairy"})
    if dt == "eggetarian":
        return not (tags & {"meat", "seafood", "pork"})
    if dt == "halal":
        return "pork" not in tags
    # vegetarian / jain / lacto-vegetarian / anything else restrictive
    return not (tags & {"meat", "seafood", "pork", "egg"})
