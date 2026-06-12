"""
User activity log — the signal source for the dashboard + recommendation engine.

Every meaningful action (a restaurant search, opening a place, a voice/cart order)
is appended here. It is intentionally lightweight and degrades to a no-op if the
write fails — analytics must never break a user-facing request. Reads power the
dashboard and seed the recommender.
"""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from ..db.database import SessionLocal, session_scope
from ..db.models import UserActivity

VALID_KINDS = {"search", "view", "dish_view", "order"}


def record(
    user_id: str,
    kind: str,
    *,
    query: Optional[str] = None,
    restaurant_id: Optional[str] = None,
    restaurant_name: Optional[str] = None,
    cuisine: Optional[str] = None,
    domain: str = "restaurant",
    payload: Optional[dict[str, Any]] = None,
) -> bool:
    """Append one activity row. Best-effort — returns False on any failure."""
    if not user_id or kind not in VALID_KINDS:
        return False
    try:
        with session_scope() as db:
            db.add(
                UserActivity(
                    user_id=user_id,
                    kind=kind,
                    query=(query or None),
                    restaurant_id=(restaurant_id or None),
                    restaurant_name=(restaurant_name or None),
                    cuisine=(cuisine or None),
                    domain=domain or "restaurant",
                    payload=payload or {},
                )
            )
        # Mirror restaurant interactions into the knowledge graph (best-effort).
        if kind in ("view", "order") and restaurant_id:
            try:
                from .knowledge_graph_service import knowledge_graph_service

                if getattr(knowledge_graph_service, "driver", None):
                    knowledge_graph_service.track_restaurant_interaction(
                        user_id,
                        restaurant_id,
                        restaurant_name or restaurant_id,
                        cuisine or "",
                        "ordered" if kind == "order" else "viewed",
                    )
            except Exception:
                pass
        elif kind == "search" and query:
            try:
                from .knowledge_graph_service import knowledge_graph_service

                if getattr(knowledge_graph_service, "driver", None):
                    knowledge_graph_service.track_search_query(user_id, query, domain)
            except Exception:
                pass
        return True
    except Exception as e:
        logger.debug(f"activity record skipped: {e}")
        return False


def _row_to_dict(row: UserActivity) -> dict[str, Any]:
    return {
        "id": row.id,
        "kind": row.kind,
        "query": row.query,
        "restaurant_id": row.restaurant_id,
        "restaurant_name": row.restaurant_name,
        "cuisine": row.cuisine,
        "domain": row.domain,
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def recent(
    user_id: str, kinds: Optional[list[str]] = None, limit: int = 30
) -> list[dict[str, Any]]:
    if not user_id:
        return []
    try:
        with SessionLocal() as db:
            q = db.query(UserActivity).filter(UserActivity.user_id == user_id)
            if kinds:
                q = q.filter(UserActivity.kind.in_(kinds))
            rows = q.order_by(UserActivity.created_at.desc(), UserActivity.id.desc()).limit(int(limit)).all()
            return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"activity recent skipped: {e}")
        return []


def dashboard(user_id: str) -> dict[str, Any]:
    """Compact summary for the user's dashboard: recent searches, viewed places,
    orders, and headline counts."""
    rows = recent(user_id, limit=120)
    searches: list[dict[str, Any]] = []
    views: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []
    seen_q: set[str] = set()
    seen_v: set[str] = set()
    for r in rows:
        if r["kind"] == "search" and r["query"]:
            key = r["query"].strip().lower()
            if key and key not in seen_q:
                seen_q.add(key)
                searches.append(r)
        elif r["kind"] in ("view", "dish_view") and r["restaurant_id"]:
            if r["restaurant_id"] not in seen_v:
                seen_v.add(r["restaurant_id"])
                views.append(r)
        elif r["kind"] == "order":
            orders.append(r)
    return {
        "status": "ok",
        "counts": {
            "searches": sum(1 for r in rows if r["kind"] == "search"),
            "views": sum(1 for r in rows if r["kind"] in ("view", "dish_view")),
            "orders": len(orders),
        },
        "recent_searches": searches[:8],
        "recent_views": views[:8],
        "recent_orders": orders[:8],
    }


def signal(user_id: str) -> dict[str, Any]:
    """Aggregate the user's behavioural signal for the recommender:
    most-searched terms, most-viewed cuisines, and recently viewed place_ids."""
    rows = recent(user_id, limit=200)
    cuisines: dict[str, int] = {}
    queries: list[str] = []
    viewed_ids: list[str] = []
    for r in rows:
        if r.get("cuisine"):
            c = r["cuisine"].strip().lower()
            cuisines[c] = cuisines.get(c, 0) + (2 if r["kind"] in ("order", "view") else 1)
        if r["kind"] == "search" and r.get("query"):
            queries.append(r["query"].strip())
        if r["kind"] in ("view", "order") and r.get("restaurant_id"):
            viewed_ids.append(r["restaurant_id"])
    top_cuisines = [c for c, _ in sorted(cuisines.items(), key=lambda kv: kv[1], reverse=True)]
    # De-dupe queries preserving recency order.
    seen: set[str] = set()
    uniq_queries: list[str] = []
    for q in queries:
        k = q.lower()
        if k and k not in seen:
            seen.add(k)
            uniq_queries.append(q)
    return {
        "top_cuisines": top_cuisines[:6],
        "recent_queries": uniq_queries[:6],
        "viewed_ids": list(dict.fromkeys(viewed_ids))[:50],
    }
