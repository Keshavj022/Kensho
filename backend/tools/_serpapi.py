"""
SerpApi HTTP client (no SDK lock-in — plain httpx against serpapi.com/search).

Every call returns the parsed JSON dict, or a graceful error dict
{"_error": "...", "_message": "..."} when the key is missing or the request fails.
Tool functions branch on the "_error" key and degrade gracefully.
"""
from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from ..config import settings

SERPAPI_URL = "https://serpapi.com/search"


def not_configured() -> dict[str, Any]:
    return {
        "_error": "not_configured",
        "_message": "SERPAPI_API_KEY is not set; SerpApi tools are disabled.",
    }


def serpapi_search(params: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
    """Call SerpApi with the given engine params. api_key is injected from settings."""
    if not settings.serpapi_configured:
        return not_configured()
    query = {**params, "api_key": settings.SERPAPI_API_KEY}
    try:
        resp = httpx.get(SERPAPI_URL, params=query, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("error"):
            logger.warning(f"SerpApi {params.get('engine')} error: {data['error']}")
            return {"_error": "serpapi_error", "_message": str(data["error"])}
        return data
    except Exception as e:  # network / HTTP / json
        logger.warning(f"SerpApi {params.get('engine')} request failed: {e}")
        return {"_error": "request_failed", "_message": str(e)}
