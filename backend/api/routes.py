"""
API routes for Kensho Restaurant Agent
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
from loguru import logger

from ..models import (
    ChatRequest,
    ChatResponse,
    RecommendationRequest,
    RecommendationResponse,
    RestaurantQuery,
    AgentStatus,
    HealthResponse,
)
from ..agents import restaurant_agent
from ..services import user_service, restaurant_service, knowledge_graph_service
from ..dependencies import get_current_user, get_optional_user

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from ..config import settings

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """Get agent status"""
    from ..config import settings

    is_ready = restaurant_agent.agent is not None

    return AgentStatus(
        status="ready" if is_ready else "not_initialized",
        is_ready=is_ready,
        model=settings.DEFAULT_MODEL,
        capabilities=["chat", "recommendations", "file_search", "rag"],
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Chat with the restaurant agent
    Requires authentication for personalized responses
    """
    try:
        # Use authenticated user_id if available, otherwise use request user_id or default
        user_id = current_user["user_id"] if current_user else (request.user_id or "default")
        user = user_service.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if agent is initialized
        if not restaurant_agent.agent:
            # For development, return mock response
            logger.warning("Agent not initialized, returning mock response")
            return ChatResponse(
                message="Agent is not initialized. Please set up Azure AI Foundry credentials.",
                thread_id="mock_thread",
                follow_up_questions=[
                    "What type of cuisine are you interested in?",
                    "Do you have any dietary restrictions?",
                    "What's your location?",
                ],
            )

        # Get or create thread
        thread_id = request.thread_id
        if not thread_id:
            thread_id = await restaurant_agent.create_thread(user)

        # Send message to agent
        response = await restaurant_agent.send_message(
            thread_id=thread_id,
            message=request.message,
            user=user,
            user_id=user_id,
        )

        return ChatResponse(
            message=response,
            thread_id=thread_id,
            follow_up_questions=[
                "Would you like more restaurant suggestions?",
                "Do you have any specific cuisine preferences?",
                "Would you like to know about specific dishes?",
            ],
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get restaurant recommendations
    Requires authentication for personalized recommendations
    """
    try:
        # Use authenticated user_id if available, otherwise use request user_id or default
        user_id = current_user["user_id"] if current_user else (request.user_id or "default")
        user = user_service.get_user(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if agent is initialized
        if not restaurant_agent.agent:
            # For development, use local restaurant service
            logger.warning("Agent not initialized, using local search")

            # Parse query for filters - use location from user profile or request
            location = user.profile.location if user and user.profile.location else None
            restaurants = await restaurant_service.search_restaurants(
                query=request.user_query,
                location=location,
                dietary_type=user.dietary.type.value if user else None,
                max_results=5,
            )

            return {
                "recommendations": restaurants,
                "explanation": f"Found {len(restaurants)} restaurants matching your preferences.",
                "confidence_score": 0.7,
                "follow_up_questions": [
                    "Would you like to see more options?",
                    "Do you have a specific cuisine in mind?",
                ],
            }

        # Try to get personalized recommendations from knowledge graph first
        kg_recommendations = []
        if knowledge_graph_service.driver:
            try:
                kg_recommendations = knowledge_graph_service.get_recommended_restaurants(
                    user_id=user_id,
                    limit=5
                )
            except Exception as e:
                logger.warning(f"Could not get KG recommendations: {str(e)}")

        # Use agent for recommendations
        result = await restaurant_agent.get_recommendations(
            query=request.user_query,
            user=user,
            user_id=user_id,
        )

        # Combine KG recommendations with agent recommendations
        all_recommendations = result.get("recommendations", [])
        if kg_recommendations:
            # Merge KG recommendations (avoid duplicates)
            kg_names = {r.get("name", "") for r in all_recommendations}
            for kg_rec in kg_recommendations:
                if kg_rec.get("name") not in kg_names:
                    all_recommendations.append(kg_rec)

        return {
            "response": result["response"],
            "thread_id": result["thread_id"],
            "recommendations": all_recommendations,
            "kg_recommendations": kg_recommendations if kg_recommendations else None,
        }

    except Exception as e:
        logger.error(f"Error in recommendations endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_restaurants(query: RestaurantQuery, user_id: Optional[str] = None):
    """
    Search restaurants based on query with location support
    """
    try:
        restaurants = await restaurant_service.search_restaurants(
            query=query.query,
            location=query.location,
            latitude=query.latitude if hasattr(query, 'latitude') else None,
            longitude=query.longitude if hasattr(query, 'longitude') else None,
            cuisine=query.cuisine,
            dietary_type=query.dietary_type.value if query.dietary_type else None,
            max_results=query.max_results,
        )

        # Track search query in knowledge graph
        if knowledge_graph_service.driver and user_id:
            knowledge_graph_service.track_search_query(
                user_id=user_id,
                query=query.query,
                agent_type="restaurant",
                results_count=len(restaurants)
            )
            
            # Track restaurant views
            for restaurant in restaurants[:5]:  # Track top 5 results
                knowledge_graph_service.track_restaurant_interaction(
                    user_id=user_id,
                    restaurant_id=restaurant.get("id", restaurant.get("name", "")),
                    restaurant_name=restaurant.get("name", ""),
                    cuisine=restaurant.get("cuisine", ""),
                    interaction_type="viewed",
                    context={"search_query": query.query}
                )

        return {
            "results": restaurants,
            "count": len(restaurants),
        }

    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuisines")
async def get_cuisines():
    """Get all available cuisines"""
    try:
        cuisines = await restaurant_service.get_all_cuisines()
        return {"cuisines": cuisines}
    except Exception as e:
        logger.error(f"Error getting cuisines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations")
async def get_locations():
    """Get all available locations (deprecated - use geocoding instead)"""
    try:
        locations = await restaurant_service.get_all_locations()
        return {"locations": locations, "note": "Use geocoding API for location search"}
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user profile
    Requires authentication. Users can only view their own profile unless admin.
    """
    try:
        # Users can only view their own profile unless they're admin
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="You can only view your own profile"
            )

        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
