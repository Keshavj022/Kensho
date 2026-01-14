"""
API routes for the Travel Agent
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from loguru import logger

from ..models import (
    FlightSearchRequest,
    HotelSearchRequest,
    ItineraryRequest,
    ItineraryResponse,
    TravelChatRequest,
    TravelChatResponse,
)
from ..agents import travel_agent
from ..services import user_service, travel_service, itinerary_service, knowledge_graph_service

router = APIRouter(prefix="/travel", tags=["travel"])


@router.post("/flights/search")
async def search_flights(request: FlightSearchRequest, user_id: Optional[str] = None):
    """
    Search for flights
    """
    try:
        if not travel_agent.agent:
            # Use local service
            flights = travel_service.search_flights(
                origin=request.origin,
                destination=request.destination,
                departure_date=request.departure_date,
                return_date=request.return_date,
                passengers=request.passengers,
                travel_class=request.travel_class,
                max_price=request.max_price,
            )

            # Track search query
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_search_query(
                    user_id=user_id,
                    query=f"flights from {request.origin} to {request.destination}",
                    agent_type="travel",
                    results_count=len(flights)
                )

            return {
                "flights": flights,
                "count": len(flights),
            }

        # Use agent for search
        result = await travel_agent.search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            passengers=request.passengers,
        )

        return result

    except Exception as e:
        logger.error(f"Error searching flights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels/search")
async def search_hotels(request: HotelSearchRequest, user_id: Optional[str] = None):
    """
    Search for hotels
    """
    try:
        if not travel_agent.agent:
            # Use local service
            hotels = travel_service.search_hotels(
                location=request.location,
                check_in=request.check_in,
                check_out=request.check_out,
                guests=request.guests,
                min_rating=request.min_rating,
                max_price_per_night=request.max_price_per_night,
            )

            # Track search query and destination interaction
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_search_query(
                    user_id=user_id,
                    query=f"hotels in {request.location}",
                    agent_type="travel",
                    results_count=len(hotels)
                )
                
                # Track destination interaction
                knowledge_graph_service.track_destination_interaction(
                    user_id=user_id,
                    destination_id=request.location.lower().replace(" ", "_"),
                    destination_name=request.location,
                    country=request.location,
                    interaction_type="viewed",
                    context={
                        "check_in": request.check_in,
                        "check_out": request.check_out,
                        "guests": request.guests
                    }
                )

            return {
                "hotels": hotels,
                "count": len(hotels),
            }

        # Use agent for search
        result = await travel_agent.search_hotels(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
        )

        return result

    except Exception as e:
        logger.error(f"Error searching hotels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/itinerary/create")
async def create_itinerary(request: ItineraryRequest):
    """
    Create a complete travel itinerary with flights, hotels, and activities
    """
    try:
        # Get user data if provided
        user = None
        user_id = request.user_id or "default"
        if user_id:
            user = user_service.get_user(user_id)

        if not travel_agent.agent:
            # Use local service
            itinerary = itinerary_service.create_itinerary(request)

            # Track destination interaction
            if knowledge_graph_service.driver and user_id:
                knowledge_graph_service.track_destination_interaction(
                    user_id=user_id,
                    destination_id=request.destination.lower().replace(" ", "_"),
                    destination_name=request.destination,
                    country=request.destination,
                    interaction_type="searched",
                    context={
                        "start_date": request.start_date,
                        "end_date": request.end_date,
                        "travelers": request.travelers,
                        "budget": request.budget
                    }
                )

            return {
                "itinerary": itinerary,
                "suggestions": [
                    "Consider booking flights 2-3 months in advance for better prices",
                    "Check visa requirements for your destination",
                    "Book popular attractions in advance",
                ],
            }

        # Use agent for itinerary planning
        result = await travel_agent.plan_itinerary(request, user, user_id)

        return result

    except Exception as e:
        logger.error(f"Error creating itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/itinerary/{itinerary_id}")
async def get_itinerary(itinerary_id: str):
    """
    Get itinerary by ID
    """
    try:
        itinerary = itinerary_service.get_itinerary(itinerary_id)

        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")

        return itinerary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/itineraries")
async def get_all_itineraries():
    """
    Get all itineraries
    """
    try:
        itineraries = itinerary_service.get_all_itineraries()

        return {
            "itineraries": itineraries,
            "count": len(itineraries),
        }

    except Exception as e:
        logger.error(f"Error getting itineraries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/itinerary/{itinerary_id}")
async def delete_itinerary(itinerary_id: str):
    """
    Delete an itinerary
    """
    try:
        success = itinerary_service.delete_itinerary(itinerary_id)

        if not success:
            raise HTTPException(status_code=404, detail="Itinerary not found")

        return {"message": "Itinerary deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def travel_chat(request: TravelChatRequest):
    """
    Chat with the travel agent
    """
    try:
        # Get user data
        user_id = request.user_id or "default"
        user = user_service.get_user(user_id)

        if not travel_agent.agent:
            # Return mock response
            return {
                "message": "Travel agent is not initialized. Please set up Azure AI Foundry credentials.",
                "thread_id": "mock_thread",
                "suggestions": [
                    "Where would you like to travel?",
                    "What's your budget?",
                    "How many days do you have?",
                ],
            }

        # Get or create thread
        thread_id = request.thread_id
        if not thread_id:
            thread_id = await travel_agent.create_thread(user)

        # Send message to agent
        response = await travel_agent.send_message(
            thread_id=thread_id,
            message=request.message,
            user=user,
            user_id=user_id,
        )

        return {
            "message": response,
            "thread_id": thread_id,
            "suggestions": [
                "Can you show me flights for these dates?",
                "What hotels do you recommend?",
                "Create a complete itinerary for me",
            ],
        }

    except Exception as e:
        logger.error(f"Error in travel chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/destinations")
async def get_destinations():
    """
    Get all available destinations
    """
    try:
        destinations = travel_service.get_all_destinations()

        return {
            "destinations": destinations,
            "count": len(destinations),
        }

    except Exception as e:
        logger.error(f"Error getting destinations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/destinations/{destination_name}")
async def get_destination_info(destination_name: str):
    """
    Get detailed information about a destination
    """
    try:
        info = travel_service.get_destination_info(destination_name)

        if not info:
            raise HTTPException(status_code=404, detail="Destination not found")

        return info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting destination info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities/{location}")
async def get_activities(location: str, activity_type: Optional[str] = None):
    """
    Get activities for a location
    """
    try:
        activities = travel_service.get_activities(location, activity_type)

        return {
            "activities": activities,
            "count": len(activities),
        }

    except Exception as e:
        logger.error(f"Error getting activities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
