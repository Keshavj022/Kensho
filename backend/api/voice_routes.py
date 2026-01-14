"""
API routes for Voice Interface
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from typing import Optional
from loguru import logger
import base64

from ..models import (
    SpeechToTextRequest,
    SpeechToTextResponse,
    TextToSpeechRequest,
    TextToSpeechResponse,
    VoiceChatRequest,
    VoiceChatResponse,
)
from ..services import voice_service, user_service
from ..agents import restaurant_agent, travel_agent

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(request: SpeechToTextRequest):
    """
    Convert speech to text using Azure Speech SDK
    """
    try:
        if not voice_service.speech_config:
            raise HTTPException(
                status_code=503,
                detail="Voice service not initialized. Please set AZURE_SPEECH_KEY environment variable."
            )

        # Perform speech-to-text
        text, confidence = voice_service.speech_to_text(
            audio_data=request.audio_data,
            language=request.language.value
        )

        if not text:
            raise HTTPException(
                status_code=400,
                detail="Could not recognize speech from audio"
            )

        return SpeechToTextResponse(
            text=text,
            confidence=confidence,
            language=request.language.value
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech-to-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using Azure Speech SDK
    """
    try:
        if not voice_service.speech_config:
            raise HTTPException(
                status_code=503,
                detail="Voice service not initialized. Please set AZURE_SPEECH_KEY environment variable."
            )

        # Perform text-to-speech
        audio_data = voice_service.text_to_speech(
            text=request.text,
            voice_name=request.voice.value,
            language=request.language.value,
            speed=request.speed,
            pitch=request.pitch
        )

        if not audio_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to synthesize speech"
            )

        # Estimate duration (rough calculation)
        word_count = len(request.text.split())
        duration_ms = int((word_count / 150) * 60 * 1000)  # Assuming 150 words per minute

        return TextToSpeechResponse(
            audio_data=audio_data,
            audio_format="audio/wav",
            duration_ms=duration_ms,
            voice_used=request.voice.value
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text-to-speech: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(request: VoiceChatRequest):
    """
    Complete voice chat: Speech-to-text -> Agent -> Text-to-speech
    """
    try:
        if not voice_service.speech_config:
            raise HTTPException(
                status_code=503,
                detail="Voice service not initialized. Please set AZURE_SPEECH_KEY environment variable."
            )

        # Step 1: Speech to text
        logger.info("Converting speech to text...")
        transcribed_text, confidence = voice_service.speech_to_text(
            audio_data=request.audio_data,
            language=request.language.value
        )

        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="Could not recognize speech from audio"
            )

        logger.info(f"Transcribed: {transcribed_text}")

        # Step 2: Get agent response
        logger.info(f"Sending to {request.agent_type} agent...")

        # Get user
        user_id = request.user_id or "default"
        user = user_service.get_user(user_id)

        # Route to appropriate agent
        if request.agent_type == "restaurant":
            agent = restaurant_agent
        elif request.agent_type == "travel":
            agent = travel_agent
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {request.agent_type}"
            )

        # Get or create thread
        thread_id = request.thread_id
        if not thread_id and agent.agent:
            thread_id = await agent.create_thread(user)

        # Send message to agent
        if agent.agent:
            agent_response = await agent.send_message(
                thread_id=thread_id,
                message=transcribed_text,
                user=user
            )
        else:
            # Fallback if agent not initialized
            agent_response = f"I heard you say: {transcribed_text}. The {request.agent_type} agent is not initialized with Azure AI. Please set up Azure credentials to get AI-powered responses."

        logger.info(f"Agent response: {agent_response[:100]}...")

        # Step 3: Text to speech
        logger.info("Converting agent response to speech...")
        audio_response = voice_service.text_to_speech(
            text=agent_response,
            voice_name=request.voice.value,
            language=request.language.value
        )

        if not audio_response:
            raise HTTPException(
                status_code=500,
                detail="Failed to synthesize speech response"
            )

        return VoiceChatResponse(
            transcribed_text=transcribed_text,
            agent_response_text=agent_response,
            audio_response=audio_response,
            thread_id=thread_id,
            confidence=confidence
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    agent_type: str = "restaurant",
    language: str = "en-US"
):
    """
    Upload audio file for transcription and agent interaction
    """
    try:
        if not voice_service.speech_config:
            raise HTTPException(
                status_code=503,
                detail="Voice service not initialized"
            )

        # Read audio file
        audio_bytes = await file.read()

        # Convert to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Create voice chat request
        voice_request = VoiceChatRequest(
            audio_data=audio_base64,
            agent_type=agent_type,
            language=language
        )

        # Process with voice chat
        response = await voice_chat(voice_request)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices():
    """
    Get list of available voices
    """
    return {
        "voices": [
            {
                "id": "en-US-AvaMultilingualNeural",
                "name": "Ava (Multilingual)",
                "language": "en-US",
                "gender": "Female",
                "description": "Friendly and professional female voice"
            },
            {
                "id": "en-US-AndrewMultilingualNeural",
                "name": "Andrew (Multilingual)",
                "language": "en-US",
                "gender": "Male",
                "description": "Warm and clear male voice"
            },
            {
                "id": "en-US-EmmaMultilingualNeural",
                "name": "Emma (Multilingual)",
                "language": "en-US",
                "gender": "Female",
                "description": "Natural and expressive female voice"
            },
            {
                "id": "en-US-BrianMultilingualNeural",
                "name": "Brian (Multilingual)",
                "language": "en-US",
                "gender": "Male",
                "description": "Professional and confident male voice"
            }
        ],
        "languages": [
            {"code": "en-US", "name": "English (US)"},
            {"code": "en-GB", "name": "English (UK)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "fr-FR", "name": "French (France)"},
            {"code": "de-DE", "name": "German (Germany)"},
            {"code": "it-IT", "name": "Italian (Italy)"},
            {"code": "ja-JP", "name": "Japanese (Japan)"},
            {"code": "zh-CN", "name": "Chinese (Simplified)"}
        ]
    }


@router.get("/status")
async def voice_status():
    """
    Get voice service status
    """
    is_configured = voice_service.speech_config is not None

    return {
        "status": "ready" if is_configured else "not_configured",
        "speech_sdk_available": is_configured,
        "speech_to_text": is_configured,
        "text_to_speech": is_configured,
        "message": "Voice service ready" if is_configured else "Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION to enable voice features"
    }
