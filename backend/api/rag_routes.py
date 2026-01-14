"""
RAG (Retrieval-Augmented Generation) API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from loguru import logger

from ..services import rag_service
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    """RAG query request"""
    query: str
    agent_type: str = "restaurant"  # "restaurant" or "travel"
    max_results: int = 5
    location: Optional[str] = None
    cuisine: Optional[str] = None
    data_type: Optional[str] = None  # For travel: "destinations", "hotels", "flights"


class RAGContextRequest(BaseModel):
    """RAG context building request"""
    query: str
    agent_type: str
    user_context: Optional[str] = None
    max_chunks: int = 3
    user_id: Optional[str] = None


@router.post("/query/restaurants")
async def query_restaurants(
    request: RAGQueryRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Query restaurant data using RAG
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        results = rag_service.retrieve_restaurants(
            query=request.query,
            location=request.location,
            cuisine=request.cuisine,
            max_results=request.max_results
        )

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying restaurants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/travel")
async def query_travel(
    request: RAGQueryRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Query travel data using RAG
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        results = rag_service.retrieve_travel_info(
            query=request.query,
            data_type=request.data_type,
            max_results=request.max_results
        )

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying travel data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context")
async def build_context(
    request: RAGContextRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Build context string using RAG
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        context = rag_service.build_context(
            query=request.query,
            agent_type=request.agent_type,
            user_context=request.user_context,
            max_chunks=request.max_chunks,
            user_id=request.user_id or (current_user["user_id"] if current_user else None)
        )

        return {
            "context": context,
            "query": request.query,
            "agent_type": request.agent_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/restaurants")
async def ingest_restaurants(
    current_user: dict = Depends(require_role("admin"))
):
    """
    Ingest restaurant data into RAG system (admin only)
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        success = rag_service.ingest_restaurant_data()

        if success:
            return {"message": "Restaurant data ingested successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to ingest restaurant data"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting restaurant data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/travel")
async def ingest_travel(
    current_user: dict = Depends(require_role("admin"))
):
    """
    Ingest travel data into RAG system (admin only)
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        success = rag_service.ingest_travel_data()

        if success:
            return {"message": "Travel data ingested successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to ingest travel data"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting travel data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{collection_name}")
async def get_collection_stats(
    collection_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about a RAG collection
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        stats = rag_service.get_collection_stats(collection_name)

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset/{collection_name}")
async def reset_collection(
    collection_name: str,
    current_user: dict = Depends(require_role("admin"))
):
    """
    Reset a RAG collection (admin only)
    """
    try:
        if not rag_service.chroma_client:
            raise HTTPException(
                status_code=503,
                detail="RAG service not available. ChromaDB not configured."
            )

        success = rag_service.reset_collection(collection_name)

        if success:
            return {"message": f"Collection '{collection_name}' reset successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reset collection '{collection_name}'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health_check():
    """
    Check RAG service health
    """
    return {
        "status": "available" if rag_service.chroma_client else "unavailable",
        "chromadb_configured": rag_service.chroma_client is not None,
        "embedding_client_available": rag_service.embedding_client is not None,
        "collections": list(rag_service.collections.keys())
    }
