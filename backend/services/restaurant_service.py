"""
Restaurant service for managing restaurant data and recommendations
"""
import json
from typing import List, Optional, Dict, Any
from loguru import logger

from ..config import settings
from ..models import Restaurant


class RestaurantService:
    """Service for managing restaurant data"""

    def __init__(self):
        """Initialize restaurant service"""
        self.restaurants: List[Dict[str, Any]] = []
        self._load_restaurant_data()

    def _load_restaurant_data(self):
        """Load restaurant data from JSON file"""
        try:
            with open(settings.RESTAURANT_DATA_PATH, "r") as f:
                data = json.load(f)
                self.restaurants = data.get("restaurants", [])
                logger.info(f"Loaded {len(self.restaurants)} restaurants")
        except FileNotFoundError:
            logger.warning(f"Restaurant data file not found: {settings.RESTAURANT_DATA_PATH}")
        except Exception as e:
            logger.error(f"Error loading restaurant data: {str(e)}")

    def search_restaurants(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        cuisine: Optional[str] = None,
        dietary_type: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search restaurants based on criteria"""
        results = self.restaurants.copy()

        # Filter by location
        if location:
            results = [
                r for r in results
                if location.lower() in r.get("location", "").lower()
            ]

        # Filter by cuisine
        if cuisine:
            results = [
                r for r in results
                if cuisine.lower() in r.get("cuisine", "").lower()
            ]

        # Filter by dietary type
        if dietary_type:
            results = [
                r for r in results
                if dietary_type.lower() in [opt.lower() for opt in r.get("dietary_options", [])]
            ]

        # Filter by query (name or description)
        if query:
            query_lower = query.lower()
            results = [
                r for r in results
                if query_lower in r.get("name", "").lower()
                or query_lower in r.get("description", "").lower()
                or any(query_lower in dish.lower() for dish in r.get("popular_dishes", []))
            ]

        return results[:max_results]

    def get_restaurant_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get restaurant by name"""
        for restaurant in self.restaurants:
            if restaurant.get("name", "").lower() == name.lower():
                return restaurant
        return None

    def get_all_cuisines(self) -> List[str]:
        """Get all unique cuisines"""
        cuisines = set()
        for restaurant in self.restaurants:
            if "cuisine" in restaurant:
                cuisines.add(restaurant["cuisine"])
        return sorted(list(cuisines))

    def get_all_locations(self) -> List[str]:
        """Get all unique locations"""
        locations = set()
        for restaurant in self.restaurants:
            if "location" in restaurant:
                locations.add(restaurant["location"])
        return sorted(list(locations))


# Global restaurant service instance
restaurant_service = RestaurantService()
