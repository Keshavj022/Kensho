"""
Restaurant service for managing restaurant data and recommendations using real-time APIs
"""
from typing import List, Optional, Dict, Any
from loguru import logger

from .external_api_service import external_api_service
from .location_service import location_service


class RestaurantService:
    """Service for managing restaurant data with real-time API integration"""

    def __init__(self):
        """Initialize restaurant service"""
        # No longer loading from JSON files - using real APIs
        logger.info("Restaurant Service initialized with real-time API integration")

    async def search_restaurants(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        cuisine: Optional[str] = None,
        dietary_type: Optional[str] = None,
        radius: int = 5000,  # meters
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search restaurants based on criteria using real-time APIs
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
                logger.warning("No location provided for restaurant search")
                return []

        # Build keyword for API search
        keyword_parts = []
        if query:
            keyword_parts.append(query)
        if cuisine:
            keyword_parts.append(cuisine)
        if dietary_type:
            keyword_parts.append(dietary_type)
        keyword = " ".join(keyword_parts) if keyword_parts else None

        # Search using external APIs
        restaurants = await external_api_service.search_restaurants(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            keyword=keyword,
            max_results=max_results,
        )

        # Filter by dietary type if specified (post-processing)
        if dietary_type and restaurants:
            filtered = []
            dietary_lower = dietary_type.lower()
            for restaurant in restaurants:
                # Check if restaurant types/categories match dietary requirements
                types = restaurant.get("types", []) or restaurant.get("categories", [])
                type_str = " ".join(types).lower() if isinstance(types, list) else str(types).lower()
                
                # Common dietary keywords
                if dietary_lower in ["vegetarian", "veggie"]:
                    if any(keyword in type_str for keyword in ["vegetarian", "veggie", "plant"]):
                        filtered.append(restaurant)
                    elif "restaurant" in type_str:  # Include all restaurants if no specific filter
                        filtered.append(restaurant)
                elif dietary_lower in ["vegan"]:
                    if "vegan" in type_str:
                        filtered.append(restaurant)
                else:
                    filtered.append(restaurant)
            
            restaurants = filtered[:max_results]

        # Add distance calculation if we have user location
        if latitude and longitude:
            for restaurant in restaurants:
                rest_lat = restaurant.get("location", {}).get("latitude")
                rest_lon = restaurant.get("location", {}).get("longitude")
                if rest_lat and rest_lon:
                    distance = location_service.calculate_distance(
                        latitude, longitude, rest_lat, rest_lon
                    )
                    restaurant["distance_km"] = round(distance, 2)

        logger.info(f"Found {len(restaurants)} restaurants near {location or f'{latitude},{longitude}'}")
        return restaurants[:max_results]

    async def get_restaurant_by_name(
        self,
        name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get restaurant by name using location-based search"""
        if not latitude or not longitude:
            logger.warning("Location required for restaurant lookup")
            return None

        results = await self.search_restaurants(
            query=name,
            latitude=latitude,
            longitude=longitude,
            max_results=5,
        )

        # Find exact match
        for restaurant in results:
            if restaurant.get("name", "").lower() == name.lower():
                return restaurant

        # Return first result if no exact match
        return results[0] if results else None

    async def get_nearby_restaurants(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get nearby restaurants based on coordinates"""
        return await self.search_restaurants(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            max_results=max_results,
        )

    async def get_all_cuisines(self) -> List[str]:
        """
        Get common cuisines (static list since we can't get all from APIs)
        This could be enhanced with web search or AI categorization
        """
        return [
            "Italian", "Chinese", "Japanese", "Indian", "Mexican",
            "Thai", "French", "American", "Mediterranean", "Korean",
            "Vietnamese", "Greek", "Spanish", "Turkish", "Lebanese",
            "Brazilian", "Peruvian", "Ethiopian", "Moroccan", "Caribbean",
        ]

    async def get_all_locations(self) -> List[str]:
        """
        Get locations is no longer feasible with real APIs
        Returns empty list - locations should be provided by user
        """
        logger.info("Location list not available with real-time APIs - use geocoding instead")
        return []


# Global restaurant service instance
restaurant_service = RestaurantService()
