"""
Web search tool — Tavily (langchain-tavily).

For destinations, activities, "best dishes", and general lookups. Degrades
gracefully when TAVILY_API_KEY is unset.
"""
from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool
from loguru import logger

from ..config import settings

_tavily = None


def _get_tavily():
    """Build + cache a TavilySearch instance (reads TAVILY_API_KEY from the env)."""
    global _tavily
    if _tavily is None:
        if settings.TAVILY_API_KEY:
            os.environ.setdefault("TAVILY_API_KEY", settings.TAVILY_API_KEY)
        from langchain_tavily import TavilySearch

        _tavily = TavilySearch(max_results=5)
    return _tavily


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for current information via Tavily.

    Use for destinations, attractions/activities, "best dishes to try", opening
    info, and any general lookup not covered by the structured tools. Returns
    {status, query, answer, results:[{title, url, content, score}]}.
    """
    if not settings.tavily_configured:
        return {
            "status": "not_configured",
            "message": "TAVILY_API_KEY is not set; web search is disabled.",
            "results": [],
        }
    try:
        tavily = _get_tavily()
        raw = tavily.invoke({"query": query})
        results = [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
                "score": r.get("score"),
            }
            for r in (raw.get("results") or [])
        ]
        return {
            "status": "ok",
            "query": query,
            "answer": raw.get("answer"),
            "results": results,
        }
    except Exception as e:
        logger.warning(f"web_search failed: {e}")
        return {"status": "error", "message": str(e), "results": []}
