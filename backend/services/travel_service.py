"""
Travel service for managing flights, hotels, and destinations using real-time APIs
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from .external_api_service import external_api_service
from .location_service import location_service
from ..models import TravelClass


class TravelService:
    """Service for managing travel data with real-time API integration"""

    def __init__(self):
        """Initialize travel service"""
        # No longer loading from JSON files - using real APIs
        logger.info("Travel Service initialized with real-time API integration")

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1,
        travel_class: Optional[TravelClass] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for flights using real-time APIs
        Origin and destination should be IATA airport codes (e.g., "NYC", "LAX")
        """
        # Default to tomorrow if no date provided
        if not departure_date:
            departure_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Search using Amadeus API
        flights = await external_api_service.search_flights_amadeus(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=passengers,
        )

        # Filter by travel class and price if specified
        if travel_class or max_price:
            filtered = []
            for flight in flights:
                # Note: Amadeus API includes class in itinerary data
                # Price filtering
                if max_price:
                    price = float(flight.get("price", 0))
                    if price > max_price:
                        continue
                filtered.append(flight)
            flights = filtered

        logger.info(f"Found {len(flights)} flights from {origin} to {destination}")
        return flights

    async def search_hotels(
        self,
        location: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 1,
        min_rating: Optional[float] = None,
        max_price_per_night: Optional[float] = None,
        radius: int = 50,  # kilometers
    ) -> List[Dict[str, Any]]:
        """
        Search for hotels using real-time APIs
        Location can be provided as:
        - location string (address/city) - will be geocoded
        - latitude/longitude coordinates
        """
        # Get coordinates from location string if needed
        if not latitude or not longitude:
            if location:
                geocoded = await location_service.geocode_address(location)
                if geocoded:
                    latitude = geocoded["latitude"]
                    longitude = geocoded["longitude"]
                else:
                    logger.warning(f"Could not geocode location: {location}")
                    return []
            else:
                logger.warning("No location provided for hotel search")
                return []

        # Default dates if not provided
        if not check_in:
            check_in = datetime.now().strftime("%Y-%m-%d")
        if not check_out:
            check_out = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Search using Amadeus API
        hotels = await external_api_service.search_hotels_amadeus(
            latitude=latitude,
            longitude=longitude,
            check_in=check_in,
            check_out=check_out,
            adults=guests,
            radius=radius,
        )

        # Filter by rating and price if specified
        if min_rating or max_price_per_night:
            filtered = []
            for hotel in hotels:
                # Rating filter (if available in hotel data)
                if min_rating:
                    rating = hotel.get("rating", 0)
                    if rating < min_rating:
                        continue
                
                # Price filter (if available in hotel data)
                if max_price_per_night:
                    price = hotel.get("price", {}).get("total", 0) if isinstance(hotel.get("price"), dict) else hotel.get("price", 0)
                    if price and price > max_price_per_night:
                        continue
                
                filtered.append(hotel)
            hotels = filtered

        # Add distance calculation
        for hotel in hotels:
            hotel_lat = hotel.get("geoCode", {}).get("latitude") if isinstance(hotel.get("geoCode"), dict) else None
            hotel_lon = hotel.get("geoCode", {}).get("longitude") if isinstance(hotel.get("geoCode"), dict) else None
            if hotel_lat and hotel_lon and latitude and longitude:
                distance = location_service.calculate_distance(
                    latitude, longitude, hotel_lat, hotel_lon
                )
                hotel["distance_km"] = round(distance, 2)

        logger.info(f"Found {len(hotels)} hotels near {location or f'{latitude},{longitude}'}")
        return hotels

    async def get_destination_info(
        self,
        destination_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a destination using web search
        """
        # Use web search to get destination information
        query = f"{destination_name} travel guide attractions things to do"
        search_results = await external_api_service.web_search(query, max_results=3)

        if search_results:
            # Combine search results into destination info
            destination_info = {
                "name": destination_name,
                "description": "\n\n".join([r.get("content") or r.get("snippet", "") for r in search_results]),
                "sources": [r.get("url") for r in search_results],
            }
            return destination_info

        return None

    async def get_activities(
        self,
        location: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        activity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get activities for a location using web search
        """
        # Get coordinates if needed
        if not latitude or not longitude:
            if location:
                geocoded = await location_service.geocode_address(location)
                if geocoded:
                    latitude = geocoded["latitude"]
                    longitude = geocoded["longitude"]
                else:
                    return []

        # Search for activities using web search
        query = f"{location} activities things to do"
        if activity_type:
            query += f" {activity_type}"

        search_results = await external_api_service.web_search(query, max_results=5)

        activities = []
        for result in search_results:
            activities.append({
                "title": result.get("title"),
                "description": result.get("content") or result.get("snippet", ""),
                "url": result.get("url"),
                "type": activity_type or "general",
            })

        return activities

    async def get_all_destinations(self) -> List[str]:
        """
        Get destinations is no longer feasible with real APIs
        Returns popular destinations list - could be enhanced with web search
        """
        return [
            "New York", "London", "Paris", "Tokyo", "Dubai",
            "Singapore", "Barcelona", "Rome", "Bali", "Sydney",
            "Amsterdam", "Bangkok", "Hong Kong", "Los Angeles", "Mumbai",
        ]

    async def get_flight_by_id(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """
        Get flight by ID - would require storing flight data or re-searching
        For now, returns None as we don't cache flight data
        """
        logger.warning("Flight lookup by ID not supported with real-time APIs")
        return None

    async def get_hotel_by_id(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get hotel by ID - would require storing hotel data or re-searching
        For now, returns None as we don't cache hotel data
        """
        logger.warning("Hotel lookup by ID not supported with real-time APIs")
        return None


# Global travel service instance
travel_service = TravelService()
