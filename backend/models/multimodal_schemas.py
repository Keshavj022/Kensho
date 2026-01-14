"""
Multimodal (Image Analysis) Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ImageFormat(str, Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"


class AnalysisFeature(str, Enum):
    """Image analysis features"""
    CAPTION = "caption"
    DENSE_CAPTIONS = "dense_captions"
    OBJECTS = "objects"
    TAGS = "tags"
    TEXT = "text"  # OCR
    PEOPLE = "people"
    SMART_CROPS = "smart_crops"


class ImageAnalysisRequest(BaseModel):
    """Image analysis request"""
    image_data: str = Field(description="Base64 encoded image data or image URL")
    is_url: bool = False
    features: List[AnalysisFeature] = [AnalysisFeature.CAPTION, AnalysisFeature.TAGS]
    language: str = "en"
    gender_neutral_caption: bool = True


class ImageCaption(BaseModel):
    """Image caption result"""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class DenseCaption(BaseModel):
    """Dense caption with bounding box"""
    text: str
    confidence: float
    bounding_box: Dict[str, int]


class DetectedObject(BaseModel):
    """Detected object in image"""
    name: str
    confidence: float
    bounding_box: Dict[str, int]


class ImageTag(BaseModel):
    """Image tag"""
    name: str
    confidence: float


class DetectedText(BaseModel):
    """Detected text (OCR result)"""
    text: str
    bounding_box: Optional[List[int]] = None


class DetectedPerson(BaseModel):
    """Detected person"""
    bounding_box: Dict[str, int]
    confidence: float


class ImageAnalysisResponse(BaseModel):
    """Image analysis response"""
    caption: Optional[ImageCaption] = None
    dense_captions: List[DenseCaption] = []
    objects: List[DetectedObject] = []
    tags: List[ImageTag] = []
    text: List[DetectedText] = []
    people: List[DetectedPerson] = []
    metadata: Dict[str, Any] = {}


class FoodImageRequest(BaseModel):
    """Food image analysis request"""
    image_data: str = Field(description="Base64 encoded image data")
    is_url: bool = False
    user_id: Optional[str] = None
    additional_context: Optional[str] = None


class FoodImageResponse(BaseModel):
    """Food image analysis response"""
    detected_food: List[str]
    description: str
    restaurant_recommendations: List[Dict[str, Any]] = []
    dietary_info: Optional[Dict[str, Any]] = None
    confidence: float


class TravelImageRequest(BaseModel):
    """Travel image analysis request"""
    image_data: str = Field(description="Base64 encoded image data")
    is_url: bool = False
    user_id: Optional[str] = None
    query: Optional[str] = None


class TravelImageResponse(BaseModel):
    """Travel image analysis response"""
    location_identified: Optional[str] = None
    description: str
    landmarks: List[str] = []
    suggested_destinations: List[str] = []
    activities: List[str] = []
    confidence: float


class MultimodalChatRequest(BaseModel):
    """Multimodal chat request (text + image)"""
    message: str
    image_data: Optional[str] = None
    is_url: bool = False
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    agent_type: str = "restaurant"  # restaurant or travel


class MultimodalChatResponse(BaseModel):
    """Multimodal chat response"""
    message: str
    image_analysis: Optional[ImageAnalysisResponse] = None
    thread_id: Optional[str] = None
