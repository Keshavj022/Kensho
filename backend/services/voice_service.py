"""STT + TTS behind a small provider interface. ElevenLabs is primary;
faster-whisper is an offline STT fallback."""
from __future__ import annotations

from io import BytesIO
from typing import Optional, Protocol

from loguru import logger

from ..config import settings


class STTProvider(Protocol):
    name: str

    def available(self) -> bool: ...
    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str: ...


class TTSProvider(Protocol):
    name: str

    def available(self) -> bool: ...
    def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes: ...


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self) -> None:
        self._client = None

    def available(self) -> bool:
        return settings.elevenlabs_configured

    def _client_(self):
        if self._client is None:
            from elevenlabs.client import ElevenLabs

            self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        return self._client

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str:
        kwargs = {"file": BytesIO(audio), "model_id": settings.ELEVENLABS_STT_MODEL}
        if language:
            kwargs["language_code"] = language
        result = self._client_().speech_to_text.convert(**kwargs)
        return getattr(result, "text", "") or ""

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        audio = self._client_().text_to_speech.convert(
            text=text,
            voice_id=voice_id or settings.ELEVENLABS_VOICE_ID,
            model_id=settings.ELEVENLABS_TTS_MODEL,
            output_format=settings.ELEVENLABS_OUTPUT_FORMAT,
        )
        if isinstance(audio, (bytes, bytearray)):
            return bytes(audio)
        return b"".join(audio)

    def list_voices(self) -> list[dict]:
        client = self._client_()
        try:
            resp = client.voices.search()
        except Exception:
            resp = client.voices.get_all()
        voices = getattr(resp, "voices", resp)
        return [{"voice_id": getattr(v, "voice_id", None), "name": getattr(v, "name", None)} for v in voices]


class WhisperProvider:
    name = "faster-whisper"

    def __init__(self) -> None:
        self._model = None

    def available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401

            return True
        except Exception:
            return False

    def _model_(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
        return self._model

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str:
        segments, _info = self._model_().transcribe(BytesIO(audio), language=language)
        return "".join(seg.text for seg in segments).strip()


class VoiceService:
    def __init__(self) -> None:
        self._elevenlabs = ElevenLabsProvider()
        self._whisper = WhisperProvider()

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> dict:
        for provider in (self._elevenlabs, self._whisper):
            if provider.available():
                try:
                    text = provider.transcribe(audio, language=language)
                    return {"status": "ok", "text": text, "provider": provider.name}
                except Exception as e:
                    logger.warning(f"STT via {provider.name} failed: {e}")
        return {
            "status": "not_configured",
            "message": "No STT provider available (set ELEVENLABS_API_KEY or install faster-whisper).",
            "text": "",
        }

    def synthesize(self, text: str, voice_id: Optional[str] = None) -> dict:
        if not self._elevenlabs.available():
            return {"status": "not_configured", "message": "ELEVENLABS_API_KEY not set", "audio": None}
        try:
            audio = self._elevenlabs.synthesize(text, voice_id=voice_id)
            return {"status": "ok", "audio": audio, "mime": "audio/mpeg", "provider": "elevenlabs"}
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            return {"status": "error", "message": str(e), "audio": None}

    def list_voices(self) -> dict:
        if not self._elevenlabs.available():
            return {"status": "not_configured", "voices": []}
        try:
            return {"status": "ok", "voices": self._elevenlabs.list_voices()}
        except Exception as e:
            return {"status": "error", "message": str(e), "voices": []}


voice_service = VoiceService()
