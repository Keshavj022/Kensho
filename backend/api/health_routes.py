"""Health endpoints — /health returns an overall + per-subsystem snapshot (always
200), with per-subsystem checks under /health/{db,kg,rag,llm,azure}."""
from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from ..config import settings

router = APIRouter(prefix="/health", tags=["health"])


def _check_db() -> dict:
    try:
        from sqlalchemy import text

        from ..db.database import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "detail": f"connected ({settings.DATABASE_URL.split('://')[0]})"}
    except Exception as e:  # pragma: no cover - defensive
        return {"status": "error", "detail": str(e)}


def _check_kg() -> dict:
    if not settings.neo4j_configured:
        return {"status": "not_configured", "detail": "NEO4J_PASSWORD not set"}
    try:
        from ..services.knowledge_graph_service import knowledge_graph_service

        if getattr(knowledge_graph_service, "driver", None):
            return {"status": "ok", "detail": "Neo4j connected"}
        return {"status": "unavailable", "detail": "Neo4j configured but not reachable"}
    except Exception as e:
        return {"status": "unavailable", "detail": str(e)}


def _check_rag() -> dict:
    try:
        from ..services.rag_service import rag_service

        if getattr(rag_service, "chroma_client", None):
            return {"status": "ok", "detail": "ChromaDB ready"}
        return {"status": "unavailable", "detail": "ChromaDB not initialized"}
    except ModuleNotFoundError:
        return {"status": "unavailable", "detail": "chromadb not installed"}
    except Exception as e:
        return {"status": "unavailable", "detail": str(e)}


def _check_llm() -> dict:
    """Reports the active chat provider (Azure OpenAI → Gemini → Ollama)."""
    try:
        from ..services.llm import providers_in_order

        order = providers_in_order()
        if not order:
            return {"status": "not_configured", "detail": "Set AZURE_OPENAI_* or GEMINI_API_KEY, or enable Ollama"}
        provider = order[0]
        label = {
            "azure": f"Azure OpenAI ({settings.AZURE_OPENAI_DEPLOYMENT})",
            "gemini": f"Gemini ({settings.GEMINI_MODEL})",
            "ollama": f"Ollama ({settings.OLLAMA_MODEL})",
        }.get(provider, provider)
        return {"status": "ok", "detail": f"{label} ready", "provider": provider, "fallbacks": order[1:]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def _check_azure() -> dict:
    bits = []
    if settings.azure_openai_configured:
        bits.append("openai")
    if settings.azure_vision_configured:
        bits.append("vision")
    if settings.azure_language_configured:
        bits.append("language")
    if settings.azure_translator_configured:
        bits.append("translator")
    if not bits:
        return {"status": "not_configured", "detail": "No AZURE_* services configured"}
    return {"status": "ok", "detail": "configured: " + ", ".join(bits)}


@router.get("")
async def health() -> dict:
    """Overall health — always 200; subsystems degrade independently."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "subsystems": {
            "db": _check_db()["status"],
            "kg": _check_kg()["status"],
            "rag": _check_rag()["status"],
            "llm": _check_llm()["status"],
            "azure": _check_azure()["status"],
        },
    }


@router.get("/db")
async def health_db() -> dict:
    return _check_db()


@router.get("/kg")
async def health_kg() -> dict:
    return _check_kg()


@router.get("/rag")
async def health_rag() -> dict:
    return _check_rag()


@router.get("/llm")
async def health_llm() -> dict:
    return _check_llm()


@router.get("/azure")
async def health_azure() -> dict:
    return _check_azure()
