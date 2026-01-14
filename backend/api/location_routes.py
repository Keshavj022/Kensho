"""
API routes for location services
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from loguru import logger

from ..services import location_service

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/ip")
async def get_location_from_ip(request: Request):
    """
    Get user location from IP address
    """
    try:
        # Get client IP
        client_ip = request.client.host
        # Try to get real IP from headers (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        location = await location_service.get_location_from_ip(client_ip)
        
        if not location:
            raise HTTPException(status_code=404, detail="Could not determine location from IP")
        
        return location
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location from IP: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geocode")
async def geocode_address(address: str):
    """
    Geocode an address to coordinates
    """
    try:
        if not address:
            raise HTTPException(status_code=400, detail="Address parameter is required")
        
        location = await location_service.geocode_address(address)
        
        if not location:
            raise HTTPException(status_code=404, detail=f"Could not geocode address: {address}")
        
        return location
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocoding address: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reverse-geocode")
async def reverse_geocode(latitude: float, longitude: float):
    """
    Reverse geocode coordinates to address
    """
    try:
        location = await location_service.reverse_geocode(latitude, longitude)
        
        if not location:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not reverse geocode coordinates: {latitude}, {longitude}"
            )
        
        return location
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverse geocoding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distance")
async def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
):
    """
    Calculate distance between two coordinates in kilometers
    """
    try:
        distance = location_service.calculate_distance(lat1, lon1, lat2, lon2)
        return {
            "distance_km": round(distance, 2),
            "distance_miles": round(distance * 0.621371, 2),
            "point1": {"latitude": lat1, "longitude": lon1},
            "point2": {"latitude": lat2, "longitude": lon2},
        }
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
