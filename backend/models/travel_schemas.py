"""
Travel-specific Pydantic models for requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class TravelClass(str, Enum):
    """Flight travel class"""
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class TripType(str, Enum):
    """Trip type"""
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"
    MULTI_CITY = "multi_city"


class AccommodationType(str, Enum):
    """Accommodation type"""
    HOTEL = "hotel"
    RESORT = "resort"
    HOSTEL = "hostel"
    APARTMENT = "apartment"
    VILLA = "villa"


class ActivityType(str, Enum):
    """Activity type"""
    SIGHTSEEING = "sightseeing"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    RELAXATION = "relaxation"
    DINING = "dining"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"


class FlightSegment(BaseModel):
    """Flight segment information"""
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    duration: str
    aircraft: Optional[str] = None
    travel_class: TravelClass


class Flight(BaseModel):
    """Flight information"""
    id: str
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    segments: List[FlightSegment]
    total_duration: str
    price: float
    currency: str = "USD"
    stops: int
    airline: str
    travel_class: TravelClass
    baggage_allowance: Optional[str] = None


class Hotel(BaseModel):
    """Hotel information"""
    id: str
    name: str
    location: str
    address: str
    rating: float = Field(ge=0, le=5)
    price_per_night: float
    currency: str = "USD"
    amenities: List[str] = []
    room_type: str
    check_in: str
    check_out: str
    total_nights: int
    total_price: float
    images: List[str] = []
    description: Optional[str] = None


class Activity(BaseModel):
    """Activity/attraction information"""
    id: str
    name: str
    type: ActivityType
    location: str
    description: str
    duration: str
    price: Optional[float] = None
    currency: str = "USD"
    rating: Optional[float] = None
    booking_required: bool = False
    time_slot: Optional[str] = None


class DayItinerary(BaseModel):
    """Single day itinerary"""
    day_number: int
    date: str
    location: str
    activities: List[Activity] = []
    meals: List[Dict[str, Any]] = []
    accommodation: Optional[Hotel] = None
    notes: Optional[str] = None


class TravelItinerary(BaseModel):
    """Complete travel itinerary"""
    id: str
    trip_name: str
    destination: str
    start_date: str
    end_date: str
    total_days: int
    travelers: int
    flights: List[Flight] = []
    hotels: List[Hotel] = []
    daily_itinerary: List[DayItinerary] = []
    total_cost: float
    currency: str = "USD"
    created_at: str
    notes: Optional[str] = None


class FlightSearchRequest(BaseModel):
    """Flight search request"""
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    travel_class: TravelClass = TravelClass.ECONOMY
    trip_type: TripType = TripType.ROUND_TRIP
    max_stops: Optional[int] = None
    max_price: Optional[float] = None


class HotelSearchRequest(BaseModel):
    """Hotel search request"""
    location: str
    check_in: str
    check_out: str
    guests: int = 1
    rooms: int = 1
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_price_per_night: Optional[float] = None
    amenities: List[str] = []


class ItineraryRequest(BaseModel):
    """Itinerary planning request"""
    destination: str
    start_date: str
    end_date: str
    travelers: int = 1
    budget: Optional[float] = None
    preferences: List[str] = []
    interests: List[ActivityType] = []
    pace: str = "moderate"  # relaxed, moderate, packed
    include_flights: bool = True
    include_hotels: bool = True
    origin: Optional[str] = None
    user_id: Optional[str] = None


class ItineraryResponse(BaseModel):
    """Itinerary planning response"""
    itinerary: TravelItinerary
    suggestions: List[str] = []
    alternatives: List[Dict[str, Any]] = []
    thread_id: Optional[str] = None


class TravelChatRequest(BaseModel):
    """Travel chat request"""
    message: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class TravelChatResponse(BaseModel):
    """Travel chat response"""
    message: str
    thread_id: str
    itinerary: Optional[TravelItinerary] = None
    flights: Optional[List[Flight]] = []
    hotels: Optional[List[Hotel]] = []
    suggestions: List[str] = []
