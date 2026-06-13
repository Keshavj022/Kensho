"""Azure AI Vision (Image Analysis 4.0) — caption, tags, objects and OCR. Used by
the menu pipeline to flag menu photos and pull text. Disabled gracefully when
AZURE_VISION_* is unset."""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from ..config import settings

EMPTY: dict[str, Any] = {"description": "", "tags": [], "objects": [], "read_text": []}


class AzureVisionService:
    def __init__(self) -> None:
        self._client: Any = None
        self._features: Any = None
        self._available = False
        self._init_attempted = False

    def _try_init(self) -> None:
        if self._init_attempted:
            return
        self._init_attempted = True
        if not settings.azure_vision_configured:
            logger.info("AZURE_VISION_* not set — Azure Vision disabled")
            return
        try:
            from azure.ai.vision.imageanalysis import ImageAnalysisClient
            from azure.ai.vision.imageanalysis.models import VisualFeatures
            from azure.core.credentials import AzureKeyCredential

            self._client = ImageAnalysisClient(
                endpoint=settings.AZURE_VISION_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_VISION_KEY or ""),
            )
            self._features = [
                VisualFeatures.CAPTION,
                VisualFeatures.TAGS,
                VisualFeatures.OBJECTS,
                VisualFeatures.READ,
            ]
            self._available = True
            logger.info(f"Azure Vision client ready ({settings.AZURE_VISION_ENDPOINT})")
        except ImportError:
            logger.warning("azure-ai-vision-imageanalysis not installed — Azure Vision disabled")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure Vision init failed: {e} — disabled")

    @property
    def available(self) -> bool:
        self._try_init()
        return self._available

    @staticmethod
    def _normalise(result: Any) -> dict[str, Any]:
        out = dict(EMPTY)
        out["tags"], out["objects"], out["read_text"] = [], [], []
        if result is None:
            return out
        caption = getattr(result, "caption", None)
        if caption is not None:
            out["description"] = (getattr(caption, "text", "") or "").strip()
        tags_result = getattr(result, "tags", None)
        if tags_result is not None:
            out["tags"] = [
                (getattr(t, "name", "") or "").strip()
                for t in (getattr(tags_result, "list", None) or [])
                if getattr(t, "name", None)
            ]
        objects_result = getattr(result, "objects", None)
        if objects_result is not None:
            names: list[str] = []
            for obj in getattr(objects_result, "list", None) or []:
                tags = getattr(obj, "tags", None) or []
                name = getattr(tags[0], "name", "") if tags else getattr(obj, "name", "")
                if name:
                    names.append(name.strip())
            out["objects"] = names
        read_result = getattr(result, "read", None)
        if read_result is not None:
            lines: list[str] = []
            for block in getattr(read_result, "blocks", None) or []:
                for line in getattr(block, "lines", None) or []:
                    text = (getattr(line, "text", "") or "").strip()
                    if text:
                        lines.append(text)
            out["read_text"] = lines
        return out

    def analyze_url(self, image_url: str) -> dict[str, Any]:
        self._try_init()
        if not self._available or self._client is None:
            return dict(EMPTY)
        try:
            result = self._client.analyze_from_url(image_url=image_url, visual_features=self._features)
            return self._normalise(result)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure Vision analyze_from_url failed: {e}")
            return dict(EMPTY)

    def analyze_bytes(self, image_bytes: bytes) -> dict[str, Any]:
        self._try_init()
        if not self._available or self._client is None:
            return dict(EMPTY)
        try:
            result = self._client.analyze(image_data=image_bytes, visual_features=self._features)
            return self._normalise(result)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Azure Vision analyze (bytes) failed: {e}")
            return dict(EMPTY)

    def ocr_lines(self, image_url: str) -> list[str]:
        """Raw OCR text lines for an image (empty list when unavailable)."""
        return self.analyze_url(image_url).get("read_text", [])

    def looks_like_menu(self, image_url: str, min_lines: int = 8) -> Optional[bool]:
        """Heuristic menu classifier from OCR density: many text lines + food-ish
        tags/caption ⇒ likely a menu. Returns None when Vision is unavailable so
        callers can fall back to the LLM classifier."""
        if not self.available:
            return None
        res = self.analyze_url(image_url)
        lines = res.get("read_text", [])
        blob = " ".join([res.get("description", ""), *res.get("tags", [])]).lower()
        menuish = any(k in blob for k in ("menu", "text", "document", "price", "font", "list", "receipt"))
        return len(lines) >= min_lines and (menuish or len(lines) >= min_lines + 6)


azure_vision_service = AzureVisionService()
