"""
Kensho backend (v2) — FastAPI app.

LangChain 1.0 + LangGraph multi-agent platform (restaurants/food, travel, shopping).
Boots with any subset of API keys configured; missing keys degrade gracefully.
Routers are added milestone by milestone; this file owns app creation + lifespan.
"""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import settings
from .api.health_routes import router as health_router

# Configure logging
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

    # Relational DB — durable source of truth (always available).
    try:
        from .db.database import init_db

        init_db()
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"DB init failed: {e}")

    # Knowledge graph (optional).
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

    # Shutdown
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

# Health is mounted at the root (load balancers expect /health).
app.include_router(health_router)


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "domains": ["restaurants", "travel", "shopping"],
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
