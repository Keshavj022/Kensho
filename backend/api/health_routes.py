"""
Health endpoints.

`GET /health` always returns 200 with an overall status plus a per-subsystem
snapshot, so a missing optional service never makes the app look "down".
Per-subsystem checks live under /health/{db,kg,rag,llm}.
"""
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
    if not settings.gemini_configured:
        return {"status": "not_configured", "detail": "GEMINI_API_KEY not set"}
    try:
        from ..services.llm import get_llm  # available from milestone 2

        get_llm()  # builds a client object; does not call the API
        return {"status": "ok", "detail": f"Gemini ready ({settings.GEMINI_MODEL})"}
    except ModuleNotFoundError:
        return {"status": "configured", "detail": "GEMINI_API_KEY set"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


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
