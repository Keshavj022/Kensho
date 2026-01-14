"""
API routes for Multimodal (Image Analysis) functionality
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
from loguru import logger
import base64

from ..models import (
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    FoodImageRequest,
    FoodImageResponse,
    TravelImageRequest,
    TravelImageResponse,
    MultimodalChatRequest,
    MultimodalChatResponse,
)
from ..services import vision_service, user_service, restaurant_service, travel_service
from ..agents import restaurant_agent, travel_agent

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze image with Azure AI Vision
    """
    try:
        if not vision_service.client:
            raise HTTPException(
                status_code=503,
                detail="Vision service not initialized. Please set AZURE_VISION_KEY and AZURE_VISION_ENDPOINT."
            )

        # Validate image if not URL
        if not request.is_url:
            if not vision_service.validate_image(request.image_data):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image data or image doesn't meet size requirements"
                )

        # Analyze image
        result = vision_service.analyze_image(
            image_data=request.image_data,
            features=[f.value for f in request.features],
            is_url=request.is_url,
            language=request.language,
            gender_neutral_caption=request.gender_neutral_caption
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze image"
            )

        return ImageAnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-food", response_model=FoodImageResponse)
async def analyze_food_image(request: FoodImageRequest):
    """
    Analyze food image and get restaurant recommendations
    """
    try:
        if not vision_service.client:
            raise HTTPException(
                status_code=503,
                detail="Vision service not initialized"
            )

        # Validate image
        if not request.is_url:
            if not vision_service.validate_image(request.image_data):
                raise HTTPException(status_code=400, detail="Invalid image")

        # Analyze food image
        description, food_items, confidence = vision_service.analyze_food_image(
            image_data=request.image_data,
            is_url=request.is_url
        )

        if not description:
            raise HTTPException(status_code=500, detail="Failed to analyze food image")

        # Get user preferences
        user_id = request.user_id or "default"
        user = user_service.get_user(user_id)

        # Search for restaurants based on detected food
        recommendations = []
        if food_items:
            # Use first food item as search query
            search_query = food_items[0] if food_items else "restaurant"
            location = user.profile.location if user else None

            restaurants = restaurant_service.search_restaurants(
                query=search_query,
                location=location,
                max_results=5
            )
            recommendations = restaurants

        # Determine dietary info based on tags
        dietary_info = None
        if food_items:
            veg_keywords = ["vegetable", "salad", "vegan", "vegetarian"]
            non_veg_keywords = ["meat", "chicken", "fish", "beef", "pork"]

            has_veg = any(any(kw in item.lower() for kw in veg_keywords) for item in food_items)
            has_non_veg = any(any(kw in item.lower() for kw in non_veg_keywords) for item in food_items)

            dietary_info = {
                "vegetarian": has_veg and not has_non_veg,
                "non_vegetarian": has_non_veg,
                "detected_ingredients": food_items[:5]
            }

        return FoodImageResponse(
            detected_food=food_items,
            description=description,
            restaurant_recommendations=recommendations,
            dietary_info=dietary_info,
            confidence=confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing food image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-travel", response_model=TravelImageResponse)
async def analyze_travel_image(request: TravelImageRequest):
    """
    Analyze travel/destination image
    """
    try:
        if not vision_service.client:
            raise HTTPException(
                status_code=503,
                detail="Vision service not initialized"
            )

        # Validate image
        if not request.is_url:
            if not vision_service.validate_image(request.image_data):
                raise HTTPException(status_code=400, detail="Invalid image")

        # Analyze travel image
        description, landmarks, tags, confidence = vision_service.analyze_travel_image(
            image_data=request.image_data,
            is_url=request.is_url
        )

        if not description:
            raise HTTPException(status_code=500, detail="Failed to analyze travel image")

        # Try to identify location from tags
        location_identified = None
        city_keywords = ["city", "town", "urban"]
        if any(any(kw in tag.lower() for kw in city_keywords) for tag in tags):
            # Get available destinations
            destinations = travel_service.get_all_destinations()
            # Simple matching - can be enhanced with ML
            for dest in destinations:
                if any(dest.lower() in tag.lower() for tag in tags):
                    location_identified = dest
                    break

        # Get suggested destinations based on image
        suggested_destinations = []
        if landmarks:
            # If landmarks detected, suggest destinations with similar attractions
            all_destinations = travel_service.get_all_destinations()
            suggested_destinations = all_destinations[:3]

        # Get activities based on image content
        activities = []
        activity_map = {
            "beach": ["swimming", "surfing", "sunbathing"],
            "mountain": ["hiking", "skiing", "climbing"],
            "city": ["sightseeing", "shopping", "dining"],
            "building": ["architecture tour", "museum visit"],
            "water": ["boat tour", "water sports"],
        }

        for tag in tags:
            tag_lower = tag.lower()
            for key, acts in activity_map.items():
                if key in tag_lower:
                    activities.extend(acts)

        activities = list(set(activities))[:5]

        return TravelImageResponse(
            location_identified=location_identified,
            description=description,
            landmarks=landmarks,
            suggested_destinations=suggested_destinations,
            activities=activities,
            confidence=confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing travel image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=MultimodalChatResponse)
async def multimodal_chat(request: MultimodalChatRequest):
    """
    Chat with agent using text and optional image
    """
    try:
        # Get user
        user_id = request.user_id or "default"
        user = user_service.get_user(user_id)

        # Select agent
        if request.agent_type == "restaurant":
            agent = restaurant_agent
        elif request.agent_type == "travel":
            agent = travel_agent
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

        # Analyze image if provided
        image_analysis = None
        enhanced_message = request.message

        if request.image_data and vision_service.client:
            # Validate and analyze image
            if not request.is_url:
                if not vision_service.validate_image(request.image_data):
                    raise HTTPException(status_code=400, detail="Invalid image")

            # Analyze based on agent type
            if request.agent_type == "restaurant":
                description, food_items, confidence = vision_service.analyze_food_image(
                    image_data=request.image_data,
                    is_url=request.is_url
                )
                if description:
                    enhanced_message = f"{request.message}\n\nI'm sharing an image that shows: {description}"
                    if food_items:
                        enhanced_message += f"\nDetected food items: {', '.join(food_items[:5])}"

            elif request.agent_type == "travel":
                description, landmarks, tags, confidence = vision_service.analyze_travel_image(
                    image_data=request.image_data,
                    is_url=request.is_url
                )
                if description:
                    enhanced_message = f"{request.message}\n\nI'm sharing an image that shows: {description}"
                    if landmarks:
                        enhanced_message += f"\nVisible landmarks: {', '.join(landmarks[:3])}"

            # Store basic analysis for response
            result = vision_service.analyze_image(
                image_data=request.image_data,
                features=["caption", "tags"],
                is_url=request.is_url
            )
            if result:
                image_analysis = ImageAnalysisResponse(**result)

        # Get or create thread
        thread_id = request.thread_id
        if not thread_id and agent.agent:
            thread_id = await agent.create_thread(user)

        # Send message to agent
        if agent.agent:
            agent_response = await agent.send_message(
                thread_id=thread_id,
                message=enhanced_message,
                user=user
            )
        else:
            # Fallback
            agent_response = f"I received your message: {request.message}"
            if image_analysis:
                agent_response += f"\n\nImage shows: {image_analysis.caption.text if image_analysis.caption else 'N/A'}"

        return MultimodalChatResponse(
            message=agent_response,
            image_analysis=image_analysis,
            thread_id=thread_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multimodal chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    agent_type: str = "restaurant",
    message: str = "What do you think about this image?"
):
    """
    Upload image file for analysis
    """
    try:
        # Read image file
        image_bytes = await file.read()

        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Create multimodal chat request
        chat_request = MultimodalChatRequest(
            message=message,
            image_data=image_base64,
            is_url=False,
            agent_type=agent_type
        )

        # Process with multimodal chat
        response = await multimodal_chat(chat_request)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def multimodal_status():
    """
    Get multimodal service status
    """
    is_configured = vision_service.client is not None

    return {
        "status": "ready" if is_configured else "not_configured",
        "vision_available": is_configured,
        "features": [
            "Image Analysis",
            "Food Recognition",
            "Landmark Detection",
            "OCR",
            "Object Detection"
        ] if is_configured else [],
        "supported_formats": ["JPEG", "PNG", "GIF", "BMP", "WEBP"],
        "message": "Multimodal service ready" if is_configured else "Set AZURE_VISION_KEY and AZURE_VISION_ENDPOINT to enable multimodal features"
    }
