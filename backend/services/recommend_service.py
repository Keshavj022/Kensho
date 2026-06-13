"""Restaurant + dish recommendations, blending the taste profile, the activity log,
the knowledge graph, and the dish index. Restaurant recs are grounded in live Maps
results; everything degrades to a sensible fallback."""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from . import activity_service
from .diet import diet_allows
from .user_service import user_service


def diet_to_search(dietary_type: Optional[str]) -> Optional[str]:
    """Map a profile diet to the `dietary` search hint (only the strong filters)."""
    if dietary_type == "vegan":
        return "vegan"
    if dietary_type in ("vegetarian", "eggetarian", "jain"):
        return "vegetarian"
    return None


def _profile_and_signal(user_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        profile = user_service.get_profile_dict(user_id)
    except Exception:
        profile = {}
    try:
        sig = activity_service.signal(user_id)
    except Exception:
        sig = {"top_cuisines": [], "recent_queries": [], "viewed_ids": []}
    return profile, sig


def _intents(profile: dict[str, Any], sig: dict[str, Any]) -> list[tuple[str, str]]:
    """Ordered (query, reason) pairs to search, most personal first."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(q: Optional[str], reason: str) -> None:
        if not q:
            return
        k = q.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append((q.strip(), reason))

    for q in sig.get("recent_queries", [])[:2]:
        add(q, "Based on your recent searches")
    for c in sig.get("top_cuisines", [])[:2]:
        add(c, f"You keep exploring {c.title()}")
    for c in (profile.get("cuisines") or [])[:2]:
        add(c, f"{c.title()} is one of your favourites")
    for f in (profile.get("likes") or [])[:2]:
        add(f, f"You love {f}")
    return out


def recommend_restaurants(
    user_id: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location: Optional[str] = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Personalised, real restaurants near the diner. Grounded in live Maps results."""
    from ..tools import places_tools

    profile, sig = _profile_and_signal(user_id)
    lat = lat if lat is not None else profile.get("lat")
    lng = lng if lng is not None else profile.get("lng")
    location = location or profile.get("location") or None
    dietary = diet_to_search(profile.get("dietary_type"))
    viewed = set(sig.get("viewed_ids", []))

    if lat is None and lng is None and not location:
        return {"status": "no_location", "restaurants": [], "message": "Set your location to get recommendations."}

    intents = _intents(profile, sig)
    intents.append((None, "Highly rated near you"))  # type: ignore[arg-type]

    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    degraded_status: Optional[str] = None

    for query, reason in intents[:4]:
        if len(out) >= limit:
            break
        try:
            res = places_tools.search_restaurants.invoke(
                {
                    "query": query,
                    "location": location,
                    "lat": lat,
                    "lng": lng,
                    "radius": 6000 if (lat is not None and lng is not None) else 5000,
                    "dietary": dietary,
                    "min_rating": 4.0,
                    "max_results": 10,
                }
            )
        except Exception as e:
            logger.warning(f"recommend_restaurants search failed: {e}")
            continue
        if res.get("status") != "ok":
            degraded_status = res.get("status")
            continue
        for r in res.get("restaurants", []):
            rid = r.get("id")
            if not rid or rid in seen_ids or rid in viewed:
                continue
            seen_ids.add(rid)
            out.append({**r, "reason": reason})

    out.sort(key=lambda r: (r.get("rating") or 0), reverse=True)
    if not out and degraded_status:
        return {"status": degraded_status, "restaurants": [], "message": "Recommendations need the search backend configured."}
    return {"status": "ok", "count": len(out[:limit]), "restaurants": out[:limit]}


def recommend_dishes(user_id: str, limit: int = 12) -> dict[str, Any]:
    """Dishes the diner is likely to love, drawn from menus Kensho has read."""
    from .vector_index import collection_count, search_menu_items

    profile, sig = _profile_and_signal(user_id)
    if collection_count() == 0:
        return {"status": "empty", "dishes": [], "message": "No menus indexed yet — open a few restaurants first."}

    queries: list[str] = []
    queries += [q for q in sig.get("recent_queries", [])[:2]]
    queries += (profile.get("likes") or [])[:4]
    queries += (profile.get("cuisines") or [])[:2]
    queries += [c for c in sig.get("top_cuisines", [])[:2]]
    if not queries:
        queries = ["popular signature dish"]

    dt = profile.get("dietary_type")
    allergies = {a.lower() for a in (profile.get("allergies") or [])}
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in queries:
        if len(out) >= limit:
            break
        try:
            hits = search_menu_items(q, max_results=8)
        except Exception:
            hits = []
        for h in hits:
            hid = h.get("id")
            if not hid or hid in seen:
                continue
            name = (h.get("name") or "")
            if not diet_allows(dt, name, h.get("dietary_flags")):
                continue
            if allergies and any(a and a in name.lower() for a in allergies):
                continue
            seen.add(hid)
            out.append({**h, "reason": f"Matches “{q}”"})

    out.sort(key=lambda d: (d.get("score") or 0), reverse=True)
    if not out:
        return featured_dishes(limit, dt)
    return {"status": "ok", "count": len(out[:limit]), "dishes": out[:limit]}


def featured_dishes(limit: int = 12, dietary_type: Optional[str] = None) -> dict[str, Any]:
    """Highly-rated / signature dishes pulled from recently extracted menus, filtered
    to the diner's diet. Spreads picks across different restaurants."""
    from ..db.database import SessionLocal
    from ..db.models import MenuCache

    try:
        with SessionLocal() as db:
            rows = (
                db.query(MenuCache)
                .order_by(MenuCache.extracted_at.desc())
                .limit(60)
                .all()
            )
            menus = [(r.place_id, r.restaurant_name, r.menu_json) for r in rows]
    except Exception as e:
        logger.debug(f"featured_dishes read skipped: {e}")
        menus = []

    picks: list[dict[str, Any]] = []
    pools: list[list[dict[str, Any]]] = []
    for place_id, rname, menu_json in menus:
        items: list[dict[str, Any]] = []
        for section in (menu_json or {}).get("sections", []):
            for it in section.get("items", []):
                if not it.get("name"):
                    continue
                if not diet_allows(dietary_type, it.get("name"), it.get("dietary_flags")):
                    continue
                items.append(
                    {
                        "id": it.get("id"),
                        "name": it.get("name"),
                        "restaurant_id": place_id,
                        "restaurant_name": rname or menu_json.get("restaurant_name"),
                        "price": it.get("price"),
                        "currency": it.get("currency") or "INR",
                        "section": it.get("section"),
                        "dietary_flags": it.get("dietary_flags") or [],
                    }
                )
        items.sort(key=lambda x: (x.get("price") is None,))  # priced first
        if items:
            pools.append(items)

    idx = 0
    while pools and len(picks) < limit:
        progressed = False
        for pool in pools:
            if idx < len(pool):
                picks.append(pool[idx])
                progressed = True
                if len(picks) >= limit:
                    break
        if not progressed:
            break
        idx += 1

    status = "ok" if picks else "empty"
    return {"status": status, "count": len(picks), "dishes": picks}


def featured_restaurants(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    location: Optional[str] = None,
    dietary: Optional[str] = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Highly-rated restaurants near a point — the default 'Find places' view."""
    from ..tools import places_tools

    if lat is None and lng is None and not location:
        return {"status": "no_location", "restaurants": []}
    res = places_tools.search_restaurants.invoke(
        {
            "location": location,
            "lat": lat,
            "lng": lng,
            "radius": 6000 if (lat is not None and lng is not None) else 5000,
            "dietary": dietary,
            "min_rating": 4.0,
            "max_results": max(1, int(limit)),
        }
    )
    if res.get("status") == "ok":
        res["restaurants"] = sorted(res.get("restaurants", []), key=lambda r: (r.get("rating") or 0), reverse=True)
    return res
