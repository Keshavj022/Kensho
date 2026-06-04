"""
RAG / retrieval tools (ChromaDB).

- get_restaurant_context: relevant restaurant docs from the knowledge base.
- search_dishes: semantic dish search across all restaurants' indexed menus
  (the Gemini-embedded `menu_items` collection populated by the menu pipeline).

Degrades gracefully when Chroma / Gemini embeddings aren't available.
"""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from loguru import logger


@tool
def get_restaurant_context(query: str, user_id: Optional[str] = None) -> dict[str, Any]:
    """Retrieve relevant restaurant context from the knowledge base (RAG).

    Returns {status, count, results:[{content, metadata, relevance_score}]} of
    restaurant documents most relevant to `query`, optionally personalized for a
    `user_id`. Use for grounded restaurant background beyond live search.
    """
    from ..services.rag_service import rag_service

    if not getattr(rag_service, "chroma_client", None):
        return {"status": "not_configured", "results": []}
    try:
        results = rag_service.retrieve_restaurants(query, user_id=user_id)
        return {"status": "ok", "count": len(results), "results": results}
    except Exception as e:
        logger.warning(f"get_restaurant_context failed: {e}")
        return {"status": "error", "message": str(e), "results": []}


@tool
def search_dishes(query: str, max_results: int = 10, restaurant_id: Optional[str] = None) -> dict[str, Any]:
    """Search menu dishes across restaurants by meaning (semantic dish search).

    Finds menu items matching `query` (e.g. "spicy paneer", "creamy pasta") across
    every restaurant whose menu has been extracted, or restrict to one
    `restaurant_id`. Returns {status, count, dishes:[{id, name, restaurant_id,
    restaurant_name, price, section, dietary_flags, score}]}. Powered by the
    menu pipeline's Gemini-embedded index; returns empty until menus are extracted.
    """
    from ..services.vector_index import collection_count, search_menu_items

    try:
        dishes = search_menu_items(query, max_results=max_results, restaurant_id=restaurant_id)
        return {
            "status": "ok",
            "count": len(dishes),
            "dishes": dishes,
            "indexed_items": collection_count(),
        }
    except Exception as e:
        logger.warning(f"search_dishes failed: {e}")
        return {"status": "error", "message": str(e), "dishes": []}
