"""
Main FastAPI application for Kensho
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from .config import settings
from .api import router
from .api.travel_routes import router as travel_router
from .api.voice_routes import router as voice_router
from .api.multimodal_routes import router as multimodal_router
from .api.knowledge_graph_routes import router as kg_router
from .api.auth_routes import router as auth_router
from .api.rag_routes import router as rag_router
from .agents import restaurant_agent, travel_agent
from .services import knowledge_graph_service, rag_service


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO" if not settings.DEBUG else "DEBUG",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting Kensho application...")

    # Initialize Knowledge Graph Service
    if knowledge_graph_service.driver:
        logger.info("Knowledge Graph Service initialized successfully")
    else:
        logger.warning("Knowledge Graph Service not available (Neo4j not configured)")

    # Initialize RAG Service and ingest data
    if rag_service.chroma_client:
        logger.info("RAG Service initialized successfully")
        # Ingest restaurant data
        if rag_service.ingest_restaurant_data():
            logger.info("Restaurant data ingested into RAG system")
        # Ingest travel data
        if rag_service.ingest_travel_data():
            logger.info("Travel data ingested into RAG system")
    else:
        logger.warning("RAG Service not available (ChromaDB not configured)")

    try:
        # Initialize the restaurant agent
        await restaurant_agent.initialize()
        logger.info("Restaurant Agent initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize Restaurant Agent: {str(e)}")
        logger.info("Restaurant Agent running in local mode")

    try:
        # Initialize the travel agent
        await travel_agent.initialize()
        logger.info("Travel Agent initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize Travel Agent: {str(e)}")
        logger.info("Travel Agent running in local mode")

    yield

    # Shutdown
    logger.info("Shutting down Kensho application...")
    try:
        await restaurant_agent.cleanup()
        await travel_agent.cleanup()
        knowledge_graph_service.close()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Kensho",
    version=settings.APP_VERSION,
    description="AI-powered multi-agent platform with restaurant and travel services using Azure AI Foundry",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router, prefix=settings.API_PREFIX)  # Auth routes (no prefix needed)
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(travel_router, prefix=settings.API_PREFIX)
app.include_router(voice_router, prefix=settings.API_PREFIX)
app.include_router(multimodal_router, prefix=settings.API_PREFIX)
app.include_router(kg_router, prefix=settings.API_PREFIX)
app.include_router(rag_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Kensho",
        "version": settings.APP_VERSION,
        "status": "running",
        "agents": ["Restaurant Agent", "Travel Agent"],
        "features": ["Text Chat", "Voice Interface", "RAG", "Itinerary Planning"],
        "docs": "/docs",
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
