"""
Vision service for image analysis using Azure AI Vision
"""
import os
import base64
from typing import Optional, List, Dict, Any, Tuple
from loguru import logger
from io import BytesIO

try:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential
    VISION_AVAILABLE = True
except ImportError:
    logger.warning("Azure Vision SDK not installed")
    VISION_AVAILABLE = False

from PIL import Image

from ..config import settings


class VisionService:
    """Service for image analysis using Azure AI Vision"""

    def __init__(self):
        """Initialize vision service"""
        self.vision_key = os.getenv("AZURE_VISION_KEY")
        self.vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.client = None

        if VISION_AVAILABLE and self.vision_key and self.vision_endpoint:
            self._initialize_client()
        else:
            logger.warning("Azure Vision not configured. Image analysis will be disabled.")

    def _initialize_client(self):
        """Initialize Azure Vision client"""
        try:
            self.client = ImageAnalysisClient(
                endpoint=self.vision_endpoint,
                credential=AzureKeyCredential(self.vision_key)
            )
            logger.info("Azure Vision client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Vision client: {str(e)}")

    def analyze_image(
        self,
        image_data: str,
        features: List[str],
        is_url: bool = False,
        language: str = "en",
        gender_neutral_caption: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze image with specified features

        Args:
            image_data: Base64 encoded image or URL
            features: List of analysis features
            is_url: Whether image_data is a URL
            language: Language for captions
            gender_neutral_caption: Use gender-neutral captions

        Returns:
            Analysis results dictionary
        """
        if not self.client:
            logger.error("Vision client not initialized")
            return None

        try:
            # Map feature strings to VisualFeatures enum
            feature_map = {
                "caption": VisualFeatures.CAPTION,
                "dense_captions": VisualFeatures.DENSE_CAPTIONS,
                "objects": VisualFeatures.OBJECTS,
                "tags": VisualFeatures.TAGS,
                "text": VisualFeatures.READ,
                "people": VisualFeatures.PEOPLE,
                "smart_crops": VisualFeatures.SMART_CROPS,
            }

            visual_features = [feature_map[f] for f in features if f in feature_map]

            if not visual_features:
                visual_features = [VisualFeatures.CAPTION, VisualFeatures.TAGS]

            # Analyze image
            if is_url:
                result = self.client.analyze_from_url(
                    image_url=image_data,
                    visual_features=visual_features,
                    language=language,
                    gender_neutral_caption=gender_neutral_caption
                )
            else:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                result = self.client.analyze(
                    image_data=image_bytes,
                    visual_features=visual_features,
                    language=language,
                    gender_neutral_caption=gender_neutral_caption
                )

            # Process results
            analysis_result = {}

            # Caption
            if result.caption:
                analysis_result["caption"] = {
                    "text": result.caption.text,
                    "confidence": result.caption.confidence
                }

            # Dense captions
            if result.dense_captions:
                analysis_result["dense_captions"] = [
                    {
                        "text": cap.text,
                        "confidence": cap.confidence,
                        "bounding_box": {
                            "x": cap.bounding_box.x,
                            "y": cap.bounding_box.y,
                            "w": cap.bounding_box.w,
                            "h": cap.bounding_box.h
                        }
                    }
                    for cap in result.dense_captions.list
                ]

            # Objects
            if result.objects:
                analysis_result["objects"] = [
                    {
                        "name": obj.tags[0].name if obj.tags else "unknown",
                        "confidence": obj.tags[0].confidence if obj.tags else 0.0,
                        "bounding_box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "w": obj.bounding_box.w,
                            "h": obj.bounding_box.h
                        }
                    }
                    for obj in result.objects.list
                ]

            # Tags
            if result.tags:
                analysis_result["tags"] = [
                    {"name": tag.name, "confidence": tag.confidence}
                    for tag in result.tags.list
                ]

            # Text (OCR)
            if result.read:
                analysis_result["text"] = [
                    {"text": block.text}
                    for block in result.read.blocks
                ]

            # People
            if result.people:
                analysis_result["people"] = [
                    {
                        "bounding_box": {
                            "x": person.bounding_box.x,
                            "y": person.bounding_box.y,
                            "w": person.bounding_box.w,
                            "h": person.bounding_box.h
                        },
                        "confidence": person.confidence
                    }
                    for person in result.people.list
                ]

            # Metadata
            analysis_result["metadata"] = {
                "width": result.metadata.width,
                "height": result.metadata.height,
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return None

    def analyze_food_image(
        self,
        image_data: str,
        is_url: bool = False
    ) -> Tuple[Optional[str], List[str], float]:
        """
        Analyze food image specifically

        Returns:
            Tuple of (description, detected_food_items, confidence)
        """
        result = self.analyze_image(
            image_data=image_data,
            features=["caption", "tags", "objects"],
            is_url=is_url
        )

        if not result:
            return None, [], 0.0

        # Extract description
        description = result.get("caption", {}).get("text", "")
        confidence = result.get("caption", {}).get("confidence", 0.0)

        # Extract food-related tags
        food_items = []
        food_keywords = ["food", "dish", "meal", "cuisine", "restaurant", "plate", "bowl"]

        tags = result.get("tags", [])
        for tag in tags:
            tag_name = tag["name"].lower()
            # Include tags that are food-related or have high confidence
            if any(keyword in tag_name for keyword in food_keywords) or tag["confidence"] > 0.8:
                food_items.append(tag["name"])

        return description, food_items, confidence

    def analyze_travel_image(
        self,
        image_data: str,
        is_url: bool = False
    ) -> Tuple[Optional[str], List[str], List[str], float]:
        """
        Analyze travel/destination image

        Returns:
            Tuple of (description, landmarks, tags, confidence)
        """
        result = self.analyze_image(
            image_data=image_data,
            features=["caption", "tags", "objects", "dense_captions"],
            is_url=is_url
        )

        if not result:
            return None, [], [], 0.0

        # Extract description
        description = result.get("caption", {}).get("text", "")
        confidence = result.get("caption", {}).get("confidence", 0.0)

        # Extract landmarks and location-related tags
        landmarks = []
        location_tags = []

        location_keywords = [
            "building", "architecture", "landmark", "monument", "beach", "mountain",
            "city", "town", "street", "temple", "church", "mosque", "palace"
        ]

        tags = result.get("tags", [])
        for tag in tags:
            tag_name = tag["name"].lower()
            if any(keyword in tag_name for keyword in location_keywords):
                if tag["confidence"] > 0.7:
                    landmarks.append(tag["name"])
            location_tags.append(tag["name"])

        return description, landmarks, location_tags[:10], confidence

    def validate_image(self, image_data: str) -> bool:
        """
        Validate image data

        Args:
            image_data: Base64 encoded image

        Returns:
            True if valid, False otherwise
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(image_data)

            # Open with PIL to validate
            image = Image.open(BytesIO(image_bytes))

            # Check size constraints (Azure Vision limits)
            width, height = image.size

            if width < 50 or height < 50:
                logger.warning("Image too small (min 50x50)")
                return False

            if width > 16000 or height > 16000:
                logger.warning("Image too large (max 16000x16000)")
                return False

            # Check file size (max 20MB)
            if len(image_bytes) > 20 * 1024 * 1024:
                logger.warning("Image file too large (max 20MB)")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            return False


# Global vision service instance
vision_service = VisionService()
