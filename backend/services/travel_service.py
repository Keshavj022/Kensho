"""
Travel service for managing flights, hotels, and destinations
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..config import settings
from ..models import (
    Flight,
    Hotel,
    Activity,
    FlightSearchRequest,
    HotelSearchRequest,
    TravelClass,
)


class TravelService:
    """Service for managing travel data"""

    def __init__(self):
        """Initialize travel service"""
        self.flights: List[Dict[str, Any]] = []
        self.hotels: List[Dict[str, Any]] = []
        self.destinations: List[Dict[str, Any]] = []
        self._load_travel_data()

    def _load_travel_data(self):
        """Load travel data from JSON files"""
        try:
            # Load flights
            flights_path = settings.DATA_DIR + "/flights_data.json"
            with open(flights_path, "r") as f:
                data = json.load(f)
                self.flights = data.get("flights", [])
                logger.info(f"Loaded {len(self.flights)} flights")
        except Exception as e:
            logger.warning(f"Could not load flights data: {str(e)}")

        try:
            # Load hotels
            hotels_path = settings.DATA_DIR + "/hotels_data.json"
            with open(hotels_path, "r") as f:
                data = json.load(f)
                self.hotels = data.get("hotels", [])
                logger.info(f"Loaded {len(self.hotels)} hotels")
        except Exception as e:
            logger.warning(f"Could not load hotels data: {str(e)}")

        try:
            # Load destinations
            destinations_path = settings.DATA_DIR + "/destinations_data.json"
            with open(destinations_path, "r") as f:
                data = json.load(f)
                self.destinations = data.get("destinations", [])
                logger.info(f"Loaded {len(self.destinations)} destinations")
        except Exception as e:
            logger.warning(f"Could not load destinations data: {str(e)}")

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1,
        travel_class: Optional[TravelClass] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for flights"""
        results = []

        for flight in self.flights:
            # Filter by origin and destination
            if (origin.lower() not in flight.get("origin", "").lower() or
                destination.lower() not in flight.get("destination", "").lower()):
                continue

            # Filter by travel class
            if travel_class and flight.get("travel_class") != travel_class.value:
                continue

            # Filter by price
            if max_price and flight.get("price", 0) > max_price:
                continue

            results.append(flight)

        return results

    def search_hotels(
        self,
        location: str,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 1,
        min_rating: Optional[float] = None,
        max_price_per_night: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for hotels"""
        results = []

        for hotel in self.hotels:
            # Filter by location
            if location.lower() not in hotel.get("location", "").lower():
                continue

            # Filter by rating
            if min_rating and hotel.get("rating", 0) < min_rating:
                continue

            # Filter by price
            if max_price_per_night and hotel.get("price_per_night", 0) > max_price_per_night:
                continue

            # Calculate total nights if dates provided
            if check_in and check_out:
                try:
                    checkin_date = datetime.fromisoformat(check_in)
                    checkout_date = datetime.fromisoformat(check_out)
                    nights = (checkout_date - checkin_date).days

                    hotel_copy = hotel.copy()
                    hotel_copy["check_in"] = check_in
                    hotel_copy["check_out"] = check_out
                    hotel_copy["total_nights"] = nights
                    hotel_copy["total_price"] = hotel["price_per_night"] * nights
                    results.append(hotel_copy)
                except:
                    results.append(hotel)
            else:
                results.append(hotel)

        return results

    def get_destination_info(self, destination_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a destination"""
        for destination in self.destinations:
            if destination["name"].lower() == destination_name.lower():
                return destination
        return None

    def get_activities(
        self,
        location: str,
        activity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get activities for a location"""
        activities = []

        for destination in self.destinations:
            if location.lower() in destination["name"].lower():
                for activity in destination.get("activities", []):
                    if not activity_type or activity["type"] == activity_type:
                        activities.append(activity)

        return activities

    def get_all_destinations(self) -> List[str]:
        """Get all destination names"""
        return [dest["name"] for dest in self.destinations]

    def get_flight_by_id(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get flight by ID"""
        for flight in self.flights:
            if flight["id"] == flight_id:
                return flight
        return None

    def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel by ID"""
        for hotel in self.hotels:
            if hotel["id"] == hotel_id:
                return hotel
        return None


# Global travel service instance
travel_service = TravelService()
