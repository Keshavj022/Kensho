"""
Knowledge-graph tools (Neo4j) — delegate to the existing KnowledgeGraphService.

User preferences, interaction tracking, and personalized recommendations.
Degrades gracefully when Neo4j isn't configured/reachable (driver is None).
"""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from loguru import logger


def _kg():
    # Lazy import so the Neo4j connection isn't opened until a tool is actually used.
    from ..services.knowledge_graph_service import knowledge_graph_service

    return knowledge_graph_service


def _disabled(payload_key: str) -> dict[str, Any]:
    return {"status": "not_configured", "message": "Neo4j not configured", payload_key: [] if payload_key != "preferences" else {}}


@tool
def get_user_preferences(user_id: str) -> dict[str, Any]:
    """Get a user's learned food/cuisine preferences and dietary profile from the graph.

    Returns {status, preferences:{user, food_preferences, cuisine_preferences,
    dietary_restrictions, dietary_goals, total_interactions}}. Use to personalize
    restaurant and dish recommendations for a known `user_id`.
    """
    kg = _kg()
    if not getattr(kg, "driver", None):
        return _disabled("preferences")
    try:
        return {"status": "ok", "preferences": kg.get_user_preferences(user_id)}
    except Exception as e:
        logger.warning(f"get_user_preferences failed: {e}")
        return {"status": "error", "message": str(e), "preferences": {}}


@tool
def track_interaction(
    user_id: str,
    restaurant_id: str,
    restaurant_name: str,
    cuisine: str = "",
    interaction_type: str = "viewed",
    rating: Optional[float] = None,
) -> dict[str, Any]:
    """Record a user's interaction with a restaurant in the knowledge graph.

    `interaction_type` is one of viewed/clicked/ordered/recommended. Use this to
    learn preferences over time (e.g. after the user views or orders from a place).
    Returns {status, tracked}.
    """
    kg = _kg()
    if not getattr(kg, "driver", None):
        return {"status": "not_configured", "tracked": False}
    try:
        ok = kg.track_restaurant_interaction(
            user_id, restaurant_id, restaurant_name, cuisine, interaction_type, rating
        )
        return {"status": "ok", "tracked": bool(ok)}
    except Exception as e:
        logger.warning(f"track_interaction failed: {e}")
        return {"status": "error", "message": str(e), "tracked": False}


@tool
def recommend_restaurants(user_id: str, limit: int = 10) -> dict[str, Any]:
    """Get personalized restaurant recommendations for a user from the graph.

    Uses the hybrid (collaborative + content-based) recommender over the user's
    history. Returns {status, count, recommendations:[{id, name, cuisine,
    hybrid_score, ...}]}. Best for a returning `user_id` with interaction history.
    """
    kg = _kg()
    if not getattr(kg, "driver", None):
        return {"status": "not_configured", "recommendations": []}
    try:
        recs = kg.get_hybrid_recommendations(user_id, limit=limit)
        return {"status": "ok", "count": len(recs), "recommendations": recs}
    except Exception as e:
        logger.warning(f"recommend_restaurants failed: {e}")
        return {"status": "error", "message": str(e), "recommendations": []}
