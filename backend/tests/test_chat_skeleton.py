"""Milestone 2 — LLM factory + skeleton supervisor graph wired to /chat."""
from __future__ import annotations

import os

import pytest

import backend.agents.supervisor as sup
import backend.services.llm as llm
from backend.config import settings


def test_chat_not_configured_is_graceful(client):
    """Without GEMINI_API_KEY, /chat returns a clear message and a thread_id, not 500."""
    r = client.post("/api/v1/chat", json={"message": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["thread_id"]
    assert "not configured" in body["message"].lower()


def test_llm_factory_requires_key():
    assert llm.is_llm_available() is (settings.GEMINI_API_KEY is not None)
    if not settings.GEMINI_API_KEY:
        with pytest.raises(llm.LLMNotConfiguredError):
            llm.reset_llm_caches()
            llm.get_llm()


def test_supervisor_compiles_offline():
    """The supervisor graph must construct (create_agent + create_supervisor +
    checkpointer) without any network call — proven with a dummy key."""
    original = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = "AIza-dummy-build-check"
    try:
        llm.reset_llm_caches()
        sup.reset_supervisor()
        graph = sup.get_supervisor()
        assert hasattr(graph, "invoke")
        assert graph.checkpointer.__class__.__name__ == "SqliteSaver"
    finally:
        settings.GEMINI_API_KEY = original
        llm.reset_llm_caches()
        sup.reset_supervisor()


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="needs a real GEMINI_API_KEY")
def test_chat_live_roundtrip(client):
    """Live end-to-end: only runs when a real key is present in the environment."""
    r = client.post("/api/v1/chat", json={"message": "Say the single word: pong"})
    assert r.status_code == 200
    body = r.json()
    assert body["message"] and "not configured" not in body["message"].lower()
