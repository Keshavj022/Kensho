"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client() -> TestClient:
    # `with` triggers the FastAPI lifespan (DB init, subsystem probes).
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_tool_cache():
    """Isolate tests from the in-process tool cache."""
    from backend.tools._cache import get_cache

    get_cache().clear()
    yield
    get_cache().clear()


@pytest.fixture(autouse=True)
def _neutralize_keys(monkeypatch):
    """Run every test with NO external services configured by default, so the
    suite is deterministic whether or not the dev has a populated .env. Tests that
    exercise a configured service monkeypatch the specific key back on."""
    import backend.agents.supervisor as sup
    import backend.services.llm as _llm
    from backend.config import settings

    for key in (
        "GEMINI_API_KEY", "SERPAPI_API_KEY", "GOOGLE_MAPS_API_KEY", "GOOGLE_PLACES_API_KEY",
        "TAVILY_API_KEY", "ELEVENLABS_API_KEY", "NEO4J_PASSWORD",
    ):
        monkeypatch.setattr(settings, key, None, raising=False)
    monkeypatch.setattr(settings, "OLLAMA_ENABLED", False, raising=False)
    _llm.reset_llm_caches()
    sup.reset_supervisor()
    yield
