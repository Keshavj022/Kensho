"""
Pydantic models for request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DietaryType(str, Enum):
    """Dietary type enum"""
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non-vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"


class RestrictionType(str, Enum):
    """Restriction type enum"""
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"
    RELIGIOUS = "religious"
    PREFERENCE = "preference"


class DietaryRestriction(BaseModel):
    """Dietary restriction model"""
    type: RestrictionType
    value: str


class FoodPreference(BaseModel):
    """Food preference model"""
    preference: str  # love, like, neutral, dislike, hate
    weight: int = Field(ge=1, le=5)


class UserProfile(BaseModel):
    """User profile model"""
    name: str
    age: Optional[int] = None
    location: str = ""
    dob: Optional[str] = None
    gender: Optional[str] = None


class DietaryInfo(BaseModel):
    """Dietary information model"""
    type: DietaryType
    restrictions: List[DietaryRestriction] = []
    goals: List[str] = []


class UserPreferences(BaseModel):
    """User preferences model"""
    foods: Dict[str, FoodPreference] = {}
    cuisines: Dict[str, FoodPreference] = {}


class User(BaseModel):
    """Complete user model"""
    profile: UserProfile
    dietary: DietaryInfo
    preferences: UserPreferences


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    thread_id: str
    recommendations: Optional[List[Dict[str, Any]]] = None
    follow_up_questions: Optional[List[str]] = None


class RestaurantQuery(BaseModel):
    """Restaurant query model"""
    query: str
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    cuisine: Optional[str] = None
    dietary_type: Optional[DietaryType] = None
    max_results: int = Field(default=10, ge=1, le=50)


class Restaurant(BaseModel):
    """Restaurant model"""
    name: str
    cuisine: str
    location: str
    rating: Optional[float] = None
    price_range: Optional[str] = None
    dietary_options: List[str] = []
    popular_dishes: List[str] = []
    description: Optional[str] = None


class RecommendationRequest(BaseModel):
    """Recommendation request model"""
    user_query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    """Recommendation response model"""
    recommendations: List[Restaurant]
    explanation: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    follow_up_questions: List[str] = []


class AgentStatus(BaseModel):
    """Agent status model"""
    status: str
    is_ready: bool
    model: str
    capabilities: List[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
