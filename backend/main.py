"""FastAPI app — LangChain + LangGraph platform for food, travel and shopping.
Boots with any subset of keys; missing ones degrade gracefully."""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .api.health_routes import router as health_router
from .api.chat_routes import router as chat_router
from .api.restaurant_routes import router as restaurant_router
from .api.menu_routes import router as menu_router
from .api.travel_routes import router as travel_router
from .api.shopping_routes import router as shopping_router
from .api.voice_routes import router as voice_router
from .api.auth_routes import router as auth_router
from .api.knowledge_graph_routes import router as kg_router
from .api.location_routes import router as location_router
from .api.me_routes import router as me_router
from .api.azure_routes import router as azure_router

logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    ),
    level="DEBUG" if settings.DEBUG else "INFO",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize durable + optional subsystems; nothing here may crash the app."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")

    try:
        from .db.database import init_db

        init_db()
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"DB init failed: {e}")

    if settings.neo4j_configured:
        try:
            from .services.knowledge_graph_service import knowledge_graph_service

            if knowledge_graph_service.driver:
                logger.info("Knowledge Graph (Neo4j) connected")
            else:
                logger.warning("Neo4j configured but not reachable — KG tools will degrade")
        except Exception as e:
            logger.warning(f"Knowledge Graph unavailable: {e}")
    else:
        logger.info("Neo4j not configured — KG tools disabled")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    try:
        from .services.knowledge_graph_service import knowledge_graph_service

        knowledge_graph_service.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI multi-agent platform (restaurants/food, travel, shopping) — LangChain 1.0 + LangGraph.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(restaurant_router, prefix=settings.API_PREFIX)
app.include_router(menu_router, prefix=settings.API_PREFIX)
app.include_router(travel_router, prefix=settings.API_PREFIX)
app.include_router(shopping_router, prefix=settings.API_PREFIX)
app.include_router(voice_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(kg_router, prefix=settings.API_PREFIX)
app.include_router(location_router, prefix=settings.API_PREFIX)
app.include_router(me_router, prefix=settings.API_PREFIX)
app.include_router(azure_router, prefix=settings.API_PREFIX)


def _api_info() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "domains": ["restaurants", "travel", "shopping"],
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_PREFIX,
    }


@app.get("/api")
async def api_info() -> dict:
    """Always-JSON service info (the SPA owns '/')."""
    return _api_info()


import os

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")


def _mount_frontend() -> bool:
    """Serve the built SPA from FastAPI (single origin, no CORS). Skipped when the
    build is absent (local dev runs Vite separately)."""
    if not (settings.SERVE_FRONTEND and os.path.isdir(_FRONTEND_DIST)):
        return False
    assets = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(assets):
        app.mount("/assets", StaticFiles(directory=assets), name="assets")
    index = os.path.join(_FRONTEND_DIST, "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(index)

    logger.info(f"Serving frontend from {_FRONTEND_DIST}")
    return True


if not _mount_frontend():
    @app.get("/")
    async def root() -> dict:
        return _api_info()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
