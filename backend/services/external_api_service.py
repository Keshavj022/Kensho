"""
External API service for fetching real-time data from various APIs
Supports: Google Places, Yelp, Geoapify, Amadeus, Skyscanner, Tavily
"""
import httpx
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from ..config import settings


class ExternalAPIService:
    """Service for interacting with external APIs"""

    def __init__(self):
        """Initialize external API service"""
        # API Keys (from environment variables)
        self.google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.yelp_api_key = os.getenv("YELP_API_KEY")
        self.geoapify_api_key = os.getenv("GEOAPIFY_API_KEY")
        self.amadeus_api_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.azure_bing_search_key = os.getenv("AZURE_BING_SEARCH_KEY")
        self.azure_bing_search_endpoint = os.getenv("AZURE_BING_SEARCH_ENDPOINT")
        
        # Amadeus token cache
        self.amadeus_token: Optional[str] = None
        self.amadeus_token_expiry: Optional[datetime] = None

    # ==================== RESTAURANT APIs ====================

    async def search_restaurants_google_places(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        keyword: Optional[str] = None,
        type: str = "restaurant",
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search restaurants using Google Places API"""
        if not self.google_places_api_key:
            logger.warning("Google Places API key not configured")
            return []

        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius,
                "type": type,
                "key": self.google_places_api_key,
            }
            if keyword:
                params["keyword"] = keyword

            restaurants = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        for place in data.get("results", [])[:max_results]:
                            restaurant = {
                                "id": place.get("place_id"),
                                "name": place.get("name"),
                                "rating": place.get("rating"),
                                "user_ratings_total": place.get("user_ratings_total", 0),
                                "price_level": place.get("price_level"),
                                "vicinity": place.get("vicinity"),
                                "location": {
                                    "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                                    "longitude": place.get("geometry", {}).get("location", {}).get("lng"),
                                },
                                "types": place.get("types", []),
                                "photos": place.get("photos", [])[:1],  # First photo reference
                            }
                            restaurants.append(restaurant)
                    else:
                        logger.warning(f"Google Places API error: {data.get('status')}")
                else:
                    logger.error(f"Google Places API HTTP error: {response.status_code}")
            
            return restaurants
        except Exception as e:
            logger.error(f"Error searching restaurants with Google Places: {str(e)}")
            return []

    async def search_restaurants_geoapify(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        category: str = "catering.restaurant",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search restaurants using Geoapify Places API (free tier available)"""
        if not self.geoapify_api_key:
            logger.warning("Geoapify API key not configured")
            return []

        try:
            url = "https://api.geoapify.com/v2/places"
            params = {
                "categories": category,
                "filter": f"circle:{longitude},{latitude},{radius}",
                "limit": limit,
                "apiKey": self.geoapify_api_key,
            }

            restaurants = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for feature in data.get("features", [])[:limit]:
                        props = feature.get("properties", {})
                        restaurant = {
                            "id": props.get("place_id"),
                            "name": props.get("name"),
                            "rating": props.get("rating"),
                            "location": {
                                "latitude": feature.get("geometry", {}).get("coordinates", [])[1],
                                "longitude": feature.get("geometry", {}).get("coordinates", [])[0],
                            },
                            "address": props.get("formatted"),
                            "categories": props.get("categories", {}),
                        }
                        restaurants.append(restaurant)
                else:
                    logger.error(f"Geoapify API HTTP error: {response.status_code}")
            
            return restaurants
        except Exception as e:
            logger.error(f"Error searching restaurants with Geoapify: {str(e)}")
            return []

    async def search_restaurants_yelp(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        term: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search restaurants using Yelp Fusion API"""
        if not self.yelp_api_key:
            logger.warning("Yelp API key not configured")
            return []

        try:
            url = "https://api.yelp.com/v3/businesses/search"
            headers = {
                "Authorization": f"Bearer {self.yelp_api_key}"
            }
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "limit": limit,
                "categories": "restaurants",
            }
            if term:
                params["term"] = term

            restaurants = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for business in data.get("businesses", []):
                        restaurant = {
                            "id": business.get("id"),
                            "name": business.get("name"),
                            "rating": business.get("rating"),
                            "review_count": business.get("review_count", 0),
                            "price": business.get("price"),
                            "location": {
                                "latitude": business.get("coordinates", {}).get("latitude"),
                                "longitude": business.get("coordinates", {}).get("longitude"),
                            },
                            "address": ", ".join(business.get("location", {}).get("display_address", [])),
                            "categories": [cat.get("title") for cat in business.get("categories", [])],
                            "image_url": business.get("image_url"),
                        }
                        restaurants.append(restaurant)
                else:
                    logger.error(f"Yelp API HTTP error: {response.status_code}")
            
            return restaurants
        except Exception as e:
            logger.error(f"Error searching restaurants with Yelp: {str(e)}")
            return []

    async def search_restaurants(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        keyword: Optional[str] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search restaurants using available APIs (tries multiple in order)
        Priority: Google Places > Yelp > Geoapify
        """
        # Try Google Places first
        if self.google_places_api_key:
            results = await self.search_restaurants_google_places(
                latitude, longitude, radius, keyword, max_results=max_results
            )
            if results:
                return results

        # Try Yelp
        if self.yelp_api_key:
            results = await self.search_restaurants_yelp(
                latitude, longitude, radius, keyword, max_results=max_results
            )
            if results:
                return results

        # Try Geoapify (free tier)
        if self.geoapify_api_key:
            results = await self.search_restaurants_geoapify(
                latitude, longitude, radius, limit=max_results
            )
            if results:
                return results

        logger.warning("No restaurant API configured, returning empty results")
        return []

    # ==================== FLIGHT APIs ====================

    async def _get_amadeus_token(self) -> Optional[str]:
        """Get Amadeus API access token"""
        if self.amadeus_token and self.amadeus_token_expiry:
            if datetime.now() < self.amadeus_token_expiry:
                return self.amadeus_token

        if not self.amadeus_api_key or not self.amadeus_api_secret:
            return None

        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.amadeus_api_key,
                "client_secret": self.amadeus_api_secret,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    self.amadeus_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 1800)
                    self.amadeus_token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                    return self.amadeus_token
                else:
                    logger.error(f"Amadeus token error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting Amadeus token: {str(e)}")
            return None

    async def search_flights_amadeus(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
    ) -> List[Dict[str, Any]]:
        """Search flights using Amadeus API"""
        token = await self._get_amadeus_token()
        if not token:
            logger.warning("Amadeus API not configured or token unavailable")
            return []

        try:
            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "max": 10,
            }
            if return_date:
                params["returnDate"] = return_date

            flights = []
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for offer in data.get("data", []):
                        flight = {
                            "id": offer.get("id"),
                            "price": offer.get("price", {}).get("total"),
                            "currency": offer.get("price", {}).get("currency"),
                            "itineraries": offer.get("itineraries", []),
                            "numberOfBookableSeats": offer.get("numberOfBookableSeats"),
                        }
                        flights.append(flight)
                else:
                    logger.error(f"Amadeus flights API error: {response.status_code}")
                    logger.error(f"Response: {response.text}")
            
            return flights
        except Exception as e:
            logger.error(f"Error searching flights with Amadeus: {str(e)}")
            return []

    # ==================== HOTEL APIs ====================

    async def search_hotels_amadeus(
        self,
        latitude: float,
        longitude: float,
        check_in: str,
        check_out: str,
        adults: int = 1,
        radius: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search hotels using Amadeus API"""
        token = await self._get_amadeus_token()
        if not token:
            logger.warning("Amadeus API not configured or token unavailable")
            return []

        try:
            # First, get hotel list
            url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geocode"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "radiusUnit": "KM",
            }

            hotels = []
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    hotel_ids = [h.get("hotelId") for h in data.get("data", [])[:10]]
                    
                    # Then get hotel offers
                    if hotel_ids:
                        offers_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
                        offers_params = {
                            "hotelIds": ",".join(hotel_ids),
                            "checkInDate": check_in,
                            "checkOutDate": check_out,
                            "adults": adults,
                        }
                        offers_response = await client.get(offers_url, params=offers_params, headers=headers)
                        if offers_response.status_code == 200:
                            offers_data = offers_response.json()
                            hotels = offers_data.get("data", [])
                else:
                    logger.error(f"Amadeus hotels API error: {response.status_code}")
            
            return hotels
        except Exception as e:
            logger.error(f"Error searching hotels with Amadeus: {str(e)}")
            return []

    # ==================== WEB SEARCH APIs ====================

    async def web_search_tavily(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search the web using Tavily API (AI-focused search)"""
        if not self.tavily_api_key:
            logger.warning("Tavily API key not configured")
            return []

        try:
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
            }

            results = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("results", []):
                        results.append({
                            "title": result.get("title"),
                            "url": result.get("url"),
                            "content": result.get("content"),
                            "score": result.get("score"),
                        })
                else:
                    logger.error(f"Tavily API error: {response.status_code}")
            
            return results
        except Exception as e:
            logger.error(f"Error searching with Tavily: {str(e)}")
            return []

    async def web_search_azure_bing(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search the web using Azure Bing Search API"""
        if not self.azure_bing_search_key or not self.azure_bing_search_endpoint:
            logger.warning("Azure Bing Search API not configured")
            return []

        try:
            url = f"{self.azure_bing_search_endpoint}/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": self.azure_bing_search_key
            }
            params = {
                "q": query,
                "count": max_results,
            }

            results = []
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("webPages", {}).get("value", []):
                        results.append({
                            "title": result.get("name"),
                            "url": result.get("url"),
                            "snippet": result.get("snippet"),
                        })
                else:
                    logger.error(f"Azure Bing Search API error: {response.status_code}")
            
            return results
        except Exception as e:
            logger.error(f"Error searching with Azure Bing: {str(e)}")
            return []

    async def web_search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search the web using available APIs
        Priority: Azure Bing > Tavily
        """
        # Try Azure Bing first
        if self.azure_bing_search_key and self.azure_bing_search_endpoint:
            results = await self.web_search_azure_bing(query, max_results)
            if results:
                return results

        # Try Tavily
        if self.tavily_api_key:
            results = await self.web_search_tavily(query, max_results)
            if results:
                return results

        logger.warning("No web search API configured")
        return []


# Global external API service instance
external_api_service = ExternalAPIService()
