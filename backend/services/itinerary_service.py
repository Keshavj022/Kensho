"""
Itinerary planning service
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import uuid

from ..models import (
    TravelItinerary,
    DayItinerary,
    Activity,
    Flight,
    Hotel,
    ItineraryRequest,
)
from .travel_service import travel_service


class ItineraryService:
    """Service for creating and managing travel itineraries"""

    def __init__(self):
        """Initialize itinerary service"""
        self.itineraries: Dict[str, TravelItinerary] = {}

    def create_itinerary(
        self,
        request: ItineraryRequest,
    ) -> TravelItinerary:
        """Create a comprehensive travel itinerary"""
        try:
            # Parse dates
            start_date = datetime.fromisoformat(request.start_date)
            end_date = datetime.fromisoformat(request.end_date)
            total_days = (end_date - start_date).days + 1

            # Initialize itinerary
            itinerary_id = str(uuid.uuid4())[:8]

            # Search for flights if requested
            flights = []
            if request.include_flights and request.origin:
                flight_results = travel_service.search_flights(
                    origin=request.origin,
                    destination=request.destination,
                    departure_date=request.start_date,
                    return_date=request.end_date,
                )
                if flight_results:
                    flights = [flight_results[0]]  # Take best match

            # Search for hotels if requested
            hotels = []
            if request.include_hotels:
                hotel_results = travel_service.search_hotels(
                    location=request.destination,
                    check_in=request.start_date,
                    check_out=request.end_date,
                    guests=request.travelers,
                )
                if hotel_results:
                    # Sort by rating and take top hotels
                    sorted_hotels = sorted(
                        hotel_results,
                        key=lambda x: x.get("rating", 0),
                        reverse=True
                    )
                    hotels = sorted_hotels[:1]  # Take best hotel

            # Get destination activities
            all_activities = travel_service.get_activities(request.destination)

            # Filter activities by interests
            filtered_activities = all_activities
            if request.interests:
                filtered_activities = [
                    act for act in all_activities
                    if act["type"] in [i.value for i in request.interests]
                ]

            # Create daily itinerary
            daily_itinerary = self._create_daily_itinerary(
                start_date=start_date,
                total_days=total_days,
                destination=request.destination,
                activities=filtered_activities,
                pace=request.pace,
                hotels=hotels,
            )

            # Calculate total cost
            total_cost = 0.0

            # Add flight costs
            for flight in flights:
                total_cost += flight.get("price", 0) * request.travelers

            # Add hotel costs
            for hotel in hotels:
                total_cost += hotel.get("total_price", 0)

            # Add activity costs
            for day in daily_itinerary:
                for activity in day.get("activities", []):
                    if activity.get("price"):
                        total_cost += activity["price"] * request.travelers

            # Create itinerary object
            itinerary_data = {
                "id": itinerary_id,
                "trip_name": f"{request.destination} Adventure",
                "destination": request.destination,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "total_days": total_days,
                "travelers": request.travelers,
                "flights": flights,
                "hotels": hotels,
                "daily_itinerary": daily_itinerary,
                "total_cost": total_cost,
                "currency": "USD",
                "created_at": datetime.now().isoformat(),
                "notes": f"Itinerary created for {request.travelers} traveler(s)",
            }

            # Store itinerary
            self.itineraries[itinerary_id] = itinerary_data

            logger.info(f"Created itinerary {itinerary_id} for {request.destination}")
            return itinerary_data

        except Exception as e:
            logger.error(f"Error creating itinerary: {str(e)}")
            raise

    def _create_daily_itinerary(
        self,
        start_date: datetime,
        total_days: int,
        destination: str,
        activities: List[Dict[str, Any]],
        pace: str,
        hotels: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Create daily itinerary based on pace"""
        daily_plan = []

        # Determine activities per day based on pace
        activities_per_day = {
            "relaxed": 2,
            "moderate": 3,
            "packed": 4,
        }.get(pace, 3)

        for day_num in range(total_days):
            current_date = start_date + timedelta(days=day_num)
            date_str = current_date.strftime("%Y-%m-%d")

            # Select activities for this day
            day_activities = []
            start_idx = day_num * activities_per_day
            end_idx = min(start_idx + activities_per_day, len(activities))

            if activities:
                # Cycle through activities if needed
                for i in range(activities_per_day):
                    activity_idx = (start_idx + i) % len(activities)
                    activity = activities[activity_idx].copy()

                    # Assign time slots
                    time_slots = ["09:00 AM", "01:00 PM", "06:00 PM"]
                    if i < len(time_slots):
                        activity["time_slot"] = time_slots[i]

                    day_activities.append(activity)

            # Add meals
            meals = [
                {"type": "breakfast", "time": "08:00 AM", "suggestion": "Hotel breakfast or local cafe"},
                {"type": "lunch", "time": "12:30 PM", "suggestion": "Local restaurant near activities"},
                {"type": "dinner", "time": "07:30 PM", "suggestion": "Recommended restaurant in the area"},
            ]

            # Get hotel for this day
            hotel = hotels[0] if hotels else None

            day_plan = {
                "day_number": day_num + 1,
                "date": date_str,
                "location": destination,
                "activities": day_activities,
                "meals": meals,
                "accommodation": hotel,
                "notes": f"Day {day_num + 1} in {destination}",
            }

            daily_plan.append(day_plan)

        return daily_plan

    def get_itinerary(self, itinerary_id: str) -> Optional[Dict[str, Any]]:
        """Get itinerary by ID"""
        return self.itineraries.get(itinerary_id)

    def update_itinerary(
        self,
        itinerary_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update an existing itinerary"""
        if itinerary_id not in self.itineraries:
            return None

        itinerary = self.itineraries[itinerary_id]
        itinerary.update(updates)
        logger.info(f"Updated itinerary {itinerary_id}")
        return itinerary

    def delete_itinerary(self, itinerary_id: str) -> bool:
        """Delete an itinerary"""
        if itinerary_id in self.itineraries:
            del self.itineraries[itinerary_id]
            logger.info(f"Deleted itinerary {itinerary_id}")
            return True
        return False

    def get_all_itineraries(self) -> List[Dict[str, Any]]:
        """Get all itineraries"""
        return list(self.itineraries.values())


# Global itinerary service instance
itinerary_service = ItineraryService()
