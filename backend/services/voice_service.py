"""
Voice service for speech-to-text and text-to-speech using Azure Speech SDK
"""
import os
import base64
import io
from typing import Optional, Tuple
from loguru import logger
import azure.cognitiveservices.speech as speechsdk

from ..config import settings


class VoiceService:
    """Service for handling voice interactions using Azure Speech SDK"""

    def __init__(self):
        """Initialize voice service"""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        self.speech_config = None

        if self.speech_key:
            self._initialize_speech_config()
        else:
            logger.warning("AZURE_SPEECH_KEY not set. Voice features will be disabled.")

    def _initialize_speech_config(self):
        """Initialize Azure Speech configuration"""
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            logger.info(f"Azure Speech SDK initialized for region: {self.speech_region}")
        except Exception as e:
            logger.error(f"Error initializing Speech SDK: {str(e)}")

    def speech_to_text(
        self,
        audio_data: str,
        language: str = "en-US"
    ) -> Tuple[Optional[str], float]:
        """
        Convert speech to text

        Args:
            audio_data: Base64 encoded audio data (WAV format)
            language: Language code (e.g., "en-US")

        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        if not self.speech_config:
            logger.error("Speech SDK not initialized")
            return None, 0.0

        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)

            # Create audio stream from bytes
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_stream.write(audio_bytes)
            audio_stream.close()

            # Configure audio input
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

            # Set language
            self.speech_config.speech_recognition_language = language

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Perform recognition
            result = speech_recognizer.recognize_once()

            # Handle result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"Recognized: {result.text}")
                # Confidence score from 0.0 to 1.0 (approximated)
                confidence = 0.95 if result.text else 0.0
                return result.text, confidence

            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return None, 0.0

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                return None, 0.0

        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            return None, 0.0

    def text_to_speech(
        self,
        text: str,
        voice_name: str = "en-US-AvaMultilingualNeural",
        language: str = "en-US",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> Optional[str]:
        """
        Convert text to speech

        Args:
            text: Text to synthesize
            voice_name: Voice to use
            language: Language code
            speed: Speech rate (0.5 to 2.0)
            pitch: Pitch adjustment (0.5 to 2.0)

        Returns:
            Base64 encoded audio data (WAV format)
        """
        if not self.speech_config:
            logger.error("Speech SDK not initialized")
            return None

        try:
            # Set voice
            self.speech_config.speech_synthesis_voice_name = voice_name

            # Create audio output configuration (to memory stream)
            audio_stream = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)

            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Return audio in result
            )

            # Build SSML for better control
            ssml = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{language}'>
                <voice name='{voice_name}'>
                    <prosody rate='{speed}' pitch='{pitch}'>
                        {text}
                    </prosody>
                </voice>
            </speak>
            """

            # Synthesize speech
            result = speech_synthesizer.speak_ssml_async(ssml).get()

            # Handle result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Speech synthesis completed")
                # Convert audio data to base64
                audio_data = result.audio_data
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                return audio_base64

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation.error_details}")
                return None

        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return None

    def recognize_from_microphone(self, language: str = "en-US") -> Tuple[Optional[str], float]:
        """
        Recognize speech from default microphone

        Args:
            language: Language code

        Returns:
            Tuple of (transcribed_text, confidence_score)
        """
        if not self.speech_config:
            logger.error("Speech SDK not initialized")
            return None, 0.0

        try:
            # Set language
            self.speech_config.speech_recognition_language = language

            # Use default microphone
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            logger.info("Speak into your microphone...")

            # Perform recognition
            result = speech_recognizer.recognize_once()

            # Handle result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.info(f"Recognized: {result.text}")
                return result.text, 0.95

            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return None, 0.0

            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"Speech recognition canceled: {cancellation.reason}")
                return None, 0.0

        except Exception as e:
            logger.error(f"Error in microphone recognition: {str(e)}")
            return None, 0.0

    def speak_to_default_speaker(self, text: str, voice_name: str = "en-US-AvaMultilingualNeural") -> bool:
        """
        Speak text to default speaker

        Args:
            text: Text to speak
            voice_name: Voice to use

        Returns:
            Success status
        """
        if not self.speech_config:
            logger.error("Speech SDK not initialized")
            return False

        try:
            # Set voice
            self.speech_config.speech_synthesis_voice_name = voice_name

            # Use default speaker
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Synthesize speech
            result = speech_synthesizer.speak_text_async(text).get()

            # Handle result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Speech played successfully")
                return True
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return False

        except Exception as e:
            logger.error(f"Error speaking to speaker: {str(e)}")
            return False


# Global voice service instance
voice_service = VoiceService()
