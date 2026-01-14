"""
Voice interface Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class VoiceLanguage(str, Enum):
    """Supported voice languages"""
    EN_US = "en-US"
    EN_GB = "en-GB"
    ES_ES = "es-ES"
    FR_FR = "fr-FR"
    DE_DE = "de-DE"
    IT_IT = "it-IT"
    JA_JP = "ja-JP"
    ZH_CN = "zh-CN"


class VoiceName(str, Enum):
    """Available voice options"""
    AVA_NEURAL = "en-US-AvaMultilingualNeural"
    ANDREW_NEURAL = "en-US-AndrewMultilingualNeural"
    EMMA_NEURAL = "en-US-EmmaMultilingualNeural"
    BRIAN_NEURAL = "en-US-BrianMultilingualNeural"


class SpeechToTextRequest(BaseModel):
    """Speech-to-text request"""
    audio_data: str = Field(description="Base64 encoded audio data")
    language: VoiceLanguage = VoiceLanguage.EN_US
    user_id: Optional[str] = None
    agent_type: Optional[str] = "restaurant"  # restaurant or travel


class SpeechToTextResponse(BaseModel):
    """Speech-to-text response"""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    language: str
    duration_ms: Optional[int] = None


class TextToSpeechRequest(BaseModel):
    """Text-to-speech request"""
    text: str
    voice: VoiceName = VoiceName.AVA_NEURAL
    language: VoiceLanguage = VoiceLanguage.EN_US
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class TextToSpeechResponse(BaseModel):
    """Text-to-speech response"""
    audio_data: str = Field(description="Base64 encoded audio data")
    audio_format: str = "audio/wav"
    duration_ms: int
    voice_used: str


class VoiceChatRequest(BaseModel):
    """Voice chat request (combines STT + agent + TTS)"""
    audio_data: str = Field(description="Base64 encoded audio data")
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    agent_type: str = "restaurant"  # restaurant or travel
    language: VoiceLanguage = VoiceLanguage.EN_US
    voice: VoiceName = VoiceName.AVA_NEURAL


class VoiceChatResponse(BaseModel):
    """Voice chat response"""
    transcribed_text: str
    agent_response_text: str
    audio_response: str = Field(description="Base64 encoded audio response")
    thread_id: Optional[str] = None
    confidence: float
