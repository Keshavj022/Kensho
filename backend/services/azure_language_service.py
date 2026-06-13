"""Azure AI Language (detection + sentiment) and Azure Translator. Safe defaults
when the keys are unset."""
from __future__ import annotations

from typing import Any, Optional

import httpx
from loguru import logger

from ..config import settings

DEFAULT_LANGUAGE: dict[str, Any] = {"iso6391": "en", "name": "English", "confidence": 0.0}
_VALID_SENTIMENTS = {"positive", "neutral", "negative", "mixed"}


class AzureLanguageService:
    def __init__(self) -> None:
        self._client: Any = None
        self._available = False
        self._init_attempted = False

    def _try_init(self) -> None:
        if self._init_attempted:
            return
        self._init_attempted = True
        if not settings.azure_language_configured:
            logger.info("AZURE_LANGUAGE_* not set — Azure Language disabled")
            return
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential

            self._client = TextAnalyticsClient(
                endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_LANGUAGE_KEY or ""),
            )
            self._available = True
            logger.info(f"Azure Language client ready ({settings.AZURE_LANGUAGE_ENDPOINT})")
        except ImportError:
            logger.warning("azure-ai-textanalytics not installed — Azure Language disabled")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure Language init failed: {e} — disabled")

    @property
    def available(self) -> bool:
        self._try_init()
        return self._available

    @property
    def translator_available(self) -> bool:
        return settings.azure_translator_configured

    def detect_language(self, text: str) -> dict[str, Any]:
        self._try_init()
        if not text or not text.strip() or not self._available or self._client is None:
            return dict(DEFAULT_LANGUAGE)
        try:
            response = self._client.detect_language(documents=[text])
            if not response:
                return dict(DEFAULT_LANGUAGE)
            doc = response[0]
            if getattr(doc, "is_error", False):
                return dict(DEFAULT_LANGUAGE)
            primary = getattr(doc, "primary_language", None)
            if primary is None:
                return dict(DEFAULT_LANGUAGE)
            return {
                "iso6391": getattr(primary, "iso6391_name", "") or "en",
                "name": getattr(primary, "name", "") or "English",
                "confidence": float(getattr(primary, "confidence_score", 0.0) or 0.0),
            }
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure detect_language failed: {e}")
            return dict(DEFAULT_LANGUAGE)

    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        default = {"sentiment": "neutral", "scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}
        self._try_init()
        if not text or not text.strip() or not self._available or self._client is None:
            return default
        try:
            response = self._client.analyze_sentiment(documents=[text])
            if not response:
                return default
            doc = response[0]
            if getattr(doc, "is_error", False):
                return default
            sentiment = (getattr(doc, "sentiment", "neutral") or "neutral").lower()
            if sentiment not in _VALID_SENTIMENTS:
                sentiment = "neutral"
            scores_obj = getattr(doc, "confidence_scores", None)
            scores = (
                {
                    "positive": float(getattr(scores_obj, "positive", 0.0) or 0.0),
                    "neutral": float(getattr(scores_obj, "neutral", 0.0) or 0.0),
                    "negative": float(getattr(scores_obj, "negative", 0.0) or 0.0),
                }
                if scores_obj is not None
                else default["scores"]
            )
            return {"sentiment": sentiment, "scores": scores}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure analyze_sentiment failed: {e}")
            return default

    def _passthrough(self, text: str, target: str, source: Optional[str]) -> dict[str, Any]:
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": source or "",
            "target_language": target,
            "translated": False,
        }

    def translate(self, text: str, target_language: str, source_language: Optional[str] = None) -> dict[str, Any]:
        """Translate via Azure Translator REST. Passthrough (unchanged) on failure."""
        if not text or not text.strip() or not target_language or not settings.azure_translator_configured:
            return self._passthrough(text, target_language, source_language)
        endpoint = (settings.AZURE_TRANSLATOR_ENDPOINT or "").rstrip("/")
        if not endpoint:
            return self._passthrough(text, target_language, source_language)
        params: dict[str, Any] = {"api-version": "3.0", "to": target_language}
        if source_language:
            params["from"] = source_language
        headers = {
            "Ocp-Apim-Subscription-Key": settings.AZURE_TRANSLATOR_KEY or "",
            "Ocp-Apim-Subscription-Region": settings.AZURE_TRANSLATOR_REGION or "",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(f"{endpoint}/translate", params=params, headers=headers, json=[{"text": text}], timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure Translator failed: {e}")
            return self._passthrough(text, target_language, source_language)
        if not isinstance(data, list) or not data:
            return self._passthrough(text, target_language, source_language)
        first = data[0] or {}
        translations = first.get("translations") or []
        if not translations:
            return self._passthrough(text, target_language, source_language)
        translated = (translations[0].get("text") or "").strip()
        detected = (first.get("detectedLanguage") or {}).get("language") or source_language or ""
        return {
            "original_text": text,
            "translated_text": translated or text,
            "source_language": detected,
            "target_language": target_language,
            "translated": bool(translated),
        }


azure_language_service = AzureLanguageService()
