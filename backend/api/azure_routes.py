"""Azure feature routes — translation, language detection, image analysis, and the
dish-index reindex. Each returns a clear status when its Azure resource is unset."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..config import settings
from ..services.azure_language_service import azure_language_service
from ..services.azure_vision_service import azure_vision_service

router = APIRouter(prefix="/azure", tags=["azure"])


class TranslateBody(BaseModel):
    text: str
    target_language: str = "en"
    source_language: Optional[str] = None


class DetectBody(BaseModel):
    text: str


class VisionBody(BaseModel):
    image_url: str


@router.post("/translate")
async def translate(body: TranslateBody) -> dict:
    if not settings.azure_translator_configured:
        return {"status": "not_configured", "message": "Set AZURE_TRANSLATOR_KEY + AZURE_TRANSLATOR_REGION."}
    res = await run_in_threadpool(
        azure_language_service.translate, body.text, body.target_language, body.source_language
    )
    return {"status": "ok", **res}


@router.post("/detect-language")
async def detect_language(body: DetectBody) -> dict:
    if not settings.azure_language_configured:
        return {"status": "not_configured", "message": "Set AZURE_LANGUAGE_KEY + AZURE_LANGUAGE_ENDPOINT."}
    res = await run_in_threadpool(azure_language_service.detect_language, body.text)
    return {"status": "ok", **res}


@router.post("/vision")
async def analyze_image(body: VisionBody) -> dict:
    if not settings.azure_vision_configured:
        return {"status": "not_configured", "message": "Set AZURE_VISION_KEY + AZURE_VISION_ENDPOINT."}
    res = await run_in_threadpool(azure_vision_service.analyze_url, body.image_url)
    return {"status": "ok", **res}


@router.post("/reindex-embeddings")
async def reindex_embeddings() -> dict:
    """Rebuild the cross-restaurant dish index with the current embedding provider.

    Run once after switching embeddings (e.g. Gemini → Azure) to repopulate dish
    search from cached menus without waiting for restaurants to be reopened.
    """
    from ..services.vector_index import reindex_from_cache

    return await run_in_threadpool(reindex_from_cache)


@router.get("/health")
async def azure_health() -> dict:
    """Per-Azure-subsystem configuration snapshot + the active embedding provider."""
    embedding_provider = "azure" if settings.azure_embeddings_configured else (
        "gemini" if settings.gemini_configured else "none"
    )
    return {
        "openai": "configured" if settings.azure_openai_configured else "not_configured",
        "embeddings": "configured" if settings.azure_embeddings_configured else "not_configured",
        "embedding_provider": embedding_provider,
        "vision": "configured" if settings.azure_vision_configured else "not_configured",
        "language": "configured" if settings.azure_language_configured else "not_configured",
        "translator": "configured" if settings.azure_translator_configured else "not_configured",
    }
