"""
API routes for Knowledge Graph operations
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from ..services.knowledge_graph_service import knowledge_graph_service
from ..services.user_service import user_service
from ..models import DietaryType, RestrictionType

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


class UserOnboardingRequest(BaseModel):
    """User onboarding request"""
    user_id: str
    name: str
    age: Optional[int] = None
    location: str
    dietary_type: Optional[DietaryType] = None
    dietary_restrictions: List[Dict[str, str]] = []
    dietary_goals: List[str] = []
    food_preferences: Dict[str, Dict[str, Any]] = {}
    cuisine_preferences: Dict[str, Dict[str, Any]] = {}


class PreferenceRequest(BaseModel):
    """Preference learning request"""
    user_id: str
    preference_type: str = Field(..., description="'food' or 'cuisine'")
    item_name: str
    preference_level: str = Field(..., description="'love', 'like', 'neutral', 'dislike', 'hate'")
    weight: int = Field(default=3, ge=1, le=5)


class RestaurantInteractionRequest(BaseModel):
    """Restaurant interaction tracking request"""
    user_id: str
    restaurant_id: str
    restaurant_name: str
    cuisine: str
    interaction_type: str = Field(..., description="'viewed', 'clicked', 'ordered', 'recommended'")
    rating: Optional[float] = Field(None, ge=0, le=5)
    context: Optional[Dict[str, Any]] = None


class DestinationInteractionRequest(BaseModel):
    """Destination interaction tracking request"""
    user_id: str
    destination_id: str
    destination_name: str
    country: str
    interaction_type: str = Field(..., description="'viewed', 'searched', 'booked', 'saved'")
    context: Optional[Dict[str, Any]] = None


@router.post("/user/onboard")
async def onboard_user(request: UserOnboardingRequest):
    """
    Onboard a new user and store their profile in the knowledge graph
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available. Please configure Neo4j."
            )

        success = knowledge_graph_service.create_user(
            user_id=request.user_id,
            name=request.name,
            age=request.age,
            location=request.location,
            dietary_type=request.dietary_type.value if request.dietary_type else None
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user in knowledge graph")

        for restriction in request.dietary_restrictions:
            knowledge_graph_service.add_dietary_restriction(
                user_id=request.user_id,
                restriction_type=restriction.get("type", "preference"),
                restriction_value=restriction.get("value", "")
            )

        for goal in request.dietary_goals:
            knowledge_graph_service.add_dietary_goal(request.user_id, goal)

        for food_name, pref_data in request.food_preferences.items():
            knowledge_graph_service.add_food_preference(
                user_id=request.user_id,
                food_name=food_name,
                preference_level=pref_data.get("preference", "neutral"),
                weight=pref_data.get("weight", 3)
            )

        for cuisine_name, pref_data in request.cuisine_preferences.items():
            knowledge_graph_service.add_cuisine_preference(
                user_id=request.user_id,
                cuisine_name=cuisine_name,
                preference_level=pref_data.get("preference", "neutral"),
                weight=pref_data.get("weight", 3)
            )

        return {
            "message": "User onboarded successfully",
            "user_id": request.user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error onboarding user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """
    Get comprehensive user preferences from knowledge graph
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        preferences = knowledge_graph_service.get_user_preferences(user_id)

        if not preferences:
            raise HTTPException(status_code=404, detail="User not found in knowledge graph")

        return preferences

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/learn")
async def learn_preference(request: PreferenceRequest):
    """
    Learn and store a user preference (food or cuisine)
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        success = user_service.learn_preference(
            user_id=request.user_id,
            preference_type=request.preference_type,
            item_name=request.item_name,
            preference_level=request.preference_level,
            weight=request.weight
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to learn preference")

        return {
            "message": "Preference learned successfully",
            "user_id": request.user_id,
            "preference_type": request.preference_type,
            "item_name": request.item_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error learning preference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interactions/restaurant")
async def track_restaurant_interaction(request: RestaurantInteractionRequest):
    """
    Track user interaction with a restaurant
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        success = knowledge_graph_service.track_restaurant_interaction(
            user_id=request.user_id,
            restaurant_id=request.restaurant_id,
            restaurant_name=request.restaurant_name,
            cuisine=request.cuisine,
            interaction_type=request.interaction_type,
            rating=request.rating,
            context=request.context
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to track interaction")

        return {
            "message": "Interaction tracked successfully",
            "user_id": request.user_id,
            "restaurant_id": request.restaurant_id,
            "interaction_type": request.interaction_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking restaurant interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interactions/destination")
async def track_destination_interaction(request: DestinationInteractionRequest):
    """
    Track user interaction with a destination
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        success = knowledge_graph_service.track_destination_interaction(
            user_id=request.user_id,
            destination_id=request.destination_id,
            destination_name=request.destination_name,
            country=request.country,
            interaction_type=request.interaction_type,
            context=request.context
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to track interaction")

        return {
            "message": "Interaction tracked successfully",
            "user_id": request.user_id,
            "destination_id": request.destination_id,
            "interaction_type": request.interaction_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking destination interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/recommendations/restaurants")
async def get_personalized_restaurants(user_id: str, limit: int = 10):
    """
    Get personalized restaurant recommendations using knowledge graph
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        recommendations = knowledge_graph_service.get_recommended_restaurants(
            user_id=user_id,
            limit=limit
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/insights")
async def get_user_insights(user_id: str):
    """
    Get analytics and insights about user behavior from knowledge graph
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        insights = knowledge_graph_service.get_user_insights(user_id)

        if not insights:
            raise HTTPException(status_code=404, detail="User not found or no insights available")

        return insights

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences/trends")
async def get_preference_trends(user_id: str, days: int = 30):
    """
    Analyze user preference trends over time
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        trends = knowledge_graph_service.analyze_preference_trends(user_id, days)

        if not trends:
            raise HTTPException(status_code=404, detail="User not found or no trends available")

        return trends

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preference trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences/{item_name}/evolution")
async def get_preference_evolution(
    user_id: str,
    item_name: str,
    preference_type: str = "food"
):
    """
    Get evolution of a specific preference over time
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        if preference_type not in ["food", "cuisine"]:
            raise HTTPException(
                status_code=400,
                detail="preference_type must be 'food' or 'cuisine'"
            )

        evolution = knowledge_graph_service.get_preference_evolution(
            user_id, item_name, preference_type
        )

        return {
            "user_id": user_id,
            "item_name": item_name,
            "preference_type": preference_type,
            "evolution": evolution
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preference evolution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/recommendations/collaborative")
async def get_collaborative_recommendations(user_id: str, limit: int = 10):
    """
    Get recommendations using collaborative filtering algorithm
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        recommendations = knowledge_graph_service.get_collaborative_filtering_recommendations(
            user_id, limit
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": "collaborative_filtering",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collaborative recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/recommendations/content-based")
async def get_content_based_recommendations(user_id: str, limit: int = 10):
    """
    Get recommendations using content-based filtering algorithm
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        recommendations = knowledge_graph_service.get_content_based_recommendations(
            user_id, limit
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": "content_based",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content-based recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/recommendations/hybrid")
async def get_hybrid_recommendations(
    user_id: str,
    limit: int = 10,
    collaborative_weight: float = 0.5
):
    """
    Get hybrid recommendations combining collaborative and content-based filtering
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        if not 0 <= collaborative_weight <= 1:
            raise HTTPException(
                status_code=400,
                detail="collaborative_weight must be between 0 and 1"
            )

        recommendations = knowledge_graph_service.get_hybrid_recommendations(
            user_id, limit, collaborative_weight
        )

        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": "hybrid",
            "collaborative_weight": collaborative_weight,
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hybrid recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/similar-users")
async def get_similar_users(user_id: str, limit: int = 10):
    """
    Find users with similar preferences
    """
    try:
        if not knowledge_graph_service.driver:
            raise HTTPException(
                status_code=503,
                detail="Knowledge graph service not available"
            )

        similar_users = knowledge_graph_service.get_similar_users(user_id, limit)

        return {
            "similar_users": similar_users,
            "count": len(similar_users),
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def kg_health_check():
    """
    Check knowledge graph service health
    """
    return {
        "status": "available" if knowledge_graph_service.driver else "unavailable",
        "neo4j_configured": knowledge_graph_service.driver is not None,
        "uri": knowledge_graph_service.uri if knowledge_graph_service.uri else None
    }
