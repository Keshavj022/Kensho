"""Gemini -> Ollama LLM fallback (open-source fallback when Gemini fails)."""
from __future__ import annotations

import pytest

import backend.services.llm as llm


class _Resp:
    def __init__(self, content):
        self.content = content


class _Raise:
    def invoke(self, _x):
        raise RuntimeError("403 PERMISSION_DENIED (gemini blocked)")


class _Ok:
    def invoke(self, _x):
        return _Resp("answer-from-ollama")


def test_invoke_falls_back_to_ollama_when_gemini_fails(monkeypatch):
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(llm, "get_llm", lambda temperature=None: _Raise())
    monkeypatch.setattr(llm, "ollama_available", lambda: True)
    monkeypatch.setattr(llm, "get_ollama_llm", lambda model_name=None, temperature=None: _Ok())
    resp = llm.invoke_with_fallback("hi")
    assert resp.content == "answer-from-ollama"


def test_invoke_raises_when_no_provider(monkeypatch):
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(llm, "ollama_available", lambda: False)
    with pytest.raises(llm.LLMNotConfiguredError):
        llm.invoke_with_fallback("hi")


def test_provider_order_and_default(monkeypatch):
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(llm, "ollama_available", lambda: True)
    assert llm.providers_in_order() == ["gemini", "ollama"]
    assert llm.default_provider() == "gemini"

    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", None)
    assert llm.providers_in_order() == ["ollama"]
    assert llm.default_provider() == "ollama"


def test_embeddings_require_gemini(monkeypatch):
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(llm, "ollama_available", lambda: True)
    # Ollama doesn't provide the Gemini embedding space.
    assert llm.embeddings_available() is False
    assert llm.is_llm_available() is True  # chat still available via Ollama
