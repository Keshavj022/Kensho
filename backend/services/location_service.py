"""
Location service for detecting and managing user locations
"""
import httpx
from typing import Optional, Dict, Any, Tuple
from loguru import logger


class LocationService:
    """Service for location detection and geocoding"""

    def __init__(self):
        """Initialize location service"""
        self.ip_geolocation_api = "http://ip-api.com/json"  # Free IP geolocation
        self.geocoding_cache: Dict[str, Dict[str, Any]] = {}

    async def get_location_from_ip(self, ip_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get location from IP address using free IP geolocation service
        Returns: {lat, lon, city, region, country, timezone}
        """
        try:
            url = self.ip_geolocation_api
            if ip_address:
                url = f"{url}/{ip_address}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return {
                            "latitude": data.get("lat"),
                            "longitude": data.get("lon"),
                            "city": data.get("city"),
                            "region": data.get("regionName"),
                            "country": data.get("country"),
                            "country_code": data.get("countryCode"),
                            "timezone": data.get("timezone"),
                            "ip": data.get("query"),
                        }
                    else:
                        logger.warning(f"IP geolocation failed: {data.get('message')}")
                        return None
                else:
                    logger.error(f"IP geolocation API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting location from IP: {str(e)}")
            return None

    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode an address to coordinates using Nominatim (OpenStreetMap)
        Returns: {lat, lon, display_name, address}
        """
        if address in self.geocoding_cache:
            return self.geocoding_cache[address]

        try:
            # Using Nominatim (free, no API key required)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
            }
            headers = {
                "User-Agent": "Kensho/1.0"  # Required by Nominatim
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        result = data[0]
                        location_data = {
                            "latitude": float(result.get("lat")),
                            "longitude": float(result.get("lon")),
                            "display_name": result.get("display_name"),
                            "address": {
                                "city": result.get("address", {}).get("city") or result.get("address", {}).get("town"),
                                "state": result.get("address", {}).get("state"),
                                "country": result.get("address", {}).get("country"),
                                "postcode": result.get("address", {}).get("postcode"),
                            }
                        }
                        self.geocoding_cache[address] = location_data
                        return location_data
                    else:
                        logger.warning(f"No results found for address: {address}")
                        return None
                else:
                    logger.error(f"Geocoding API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error geocoding address: {str(e)}")
            return None

    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to address using Nominatim
        Returns: {display_name, address}
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
            }
            headers = {
                "User-Agent": "Kensho/1.0"
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "display_name": data.get("display_name"),
                            "address": data.get("address", {}),
                            "latitude": latitude,
                            "longitude": longitude,
                        }
                    else:
                        return None
                else:
                    logger.error(f"Reverse geocoding API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error reverse geocoding: {str(e)}")
            return None

    def calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates in kilometers using Haversine formula
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in kilometers

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance


# Global location service instance
location_service = LocationService()
