"""
Configuration settings for Kensho (v2 rewrite).

All secrets and volatile model IDs are environment-driven (never hardcoded).
Every external integration is optional: a missing key disables only that tool,
the app still boots and serves every other route (graceful degradation).
"""
from __future__ import annotations

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(
        # Look for a .env at the repo root first, then backend/.env.
        env_file=(os.path.join(_REPO_ROOT, ".env"), os.path.join(_BACKEND_DIR, ".env")),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # tolerate stray legacy env vars without crashing
    )

    # ------------------------------------------------------------------ App
    APP_NAME: str = "Kensho"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS is a plain comma-separated string in .env; use .cors_origins for the list.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ------------------------------------------------------------------ LLM (Gemini)
    GEMINI_API_KEY: Optional[str] = None
    # Default to a current GA Flash model; override via .env (e.g. gemini-3.5-flash).
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # Stronger model used to escalate hard / low-quality menu OCR.
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    # Gemini embedding model used for all Chroma collections (one vector space).
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GEMINI_TEMPERATURE: float = 0.2

    # ------------------------------------------------------------------ LLM fallback (Ollama, open-source)
    # When enabled, a local Ollama model is used if a Gemini call fails (or if Gemini
    # is unconfigured). The chat model MUST support tool-calling for the agents.
    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"             # tool-capable model for agents/chat
    OLLAMA_VISION_MODEL: str = "llama3.2-vision"  # used for menu OCR fallback
    OLLAMA_TEMPERATURE: float = 0.2

    # ------------------------------------------------------------------ Tool backbone
    # Google Places API (New). GOOGLE_MAPS_API_KEY is canonical; legacy fallback below.
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    # SerpApi localization — without these, results default to the US locale (USD).
    SERPAPI_GL: str = "in"  # country (in = India)
    SERPAPI_HL: str = "en"  # language
    SERPAPI_LOCATION: str = "India"
    DEFAULT_CURRENCY: str = "INR"

    # ------------------------------------------------------------------ Voice
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"  # default ElevenLabs voice
    ELEVENLABS_TTS_MODEL: str = "eleven_multilingual_v2"
    ELEVENLABS_STT_MODEL: str = "scribe_v2"
    ELEVENLABS_OUTPUT_FORMAT: str = "mp3_44100_128"
    # Offline STT fallback (faster-whisper). Disabled unless the package is installed.
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # ------------------------------------------------------------------ Knowledge graph (Neo4j)
    NEO4J_URI: Optional[str] = "bolt://localhost:7687"
    NEO4J_USERNAME: Optional[str] = "neo4j"
    NEO4J_PASSWORD: Optional[str] = None

    # ------------------------------------------------------------------ Vector store (Chroma)
    CHROMA_PATH: str = os.path.join(_REPO_ROOT, "chroma_data")

    # ------------------------------------------------------------------ Relational DB + checkpointer
    DATABASE_URL: str = "sqlite:///./kensho.db"
    CHECKPOINTER_DB_PATH: str = os.path.join(_REPO_ROOT, "kensho_checkpoints.db")

    # ------------------------------------------------------------------ Auth / JWT
    JWT_SECRET_KEY: str = "dev-insecure-change-me"  # MUST be overridden in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------ Demo account
    DEMO_PASSWORD: str = "kensho-demo-guest-2024"

    # ------------------------------------------------------------------ Caching / pipeline tuning
    MENU_CACHE_TTL_DAYS: int = 30
    SERPAPI_CACHE_TTL_HOURS: int = 6
    PLACES_CACHE_TTL_HOURS: int = 24

    # ------------------------------------------------------------------ Legacy-compat fields
    # Consumed by services not yet migrated (rag_service / kg_service / auth / user).
    DATA_DIR: str = os.path.join(_BACKEND_DIR, "data")
    USER_DATA_PATH: str = os.path.join(_BACKEND_DIR, "data", "user_data.json")
    RESTAURANT_DATA_PATH: str = os.path.join(_BACKEND_DIR, "data", "restaurant_data.json")
    CHROMADB_PATH: Optional[str] = None  # filled from CHROMA_PATH in __init__
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GOOGLE_PLACES_API_KEY: Optional[str] = None  # legacy name; falls back to GOOGLE_MAPS_API_KEY
    # Azure OpenAI deployment name referenced by the un-migrated rag_service (unused now).
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Keep the legacy CHROMADB_PATH alias pointed at the canonical path.
        if not self.CHROMADB_PATH:
            self.CHROMADB_PATH = self.CHROMA_PATH
        # Allow GOOGLE_PLACES_API_KEY to satisfy the Places key if MAPS not set.
        if not self.GOOGLE_MAPS_API_KEY and self.GOOGLE_PLACES_API_KEY:
            self.GOOGLE_MAPS_API_KEY = self.GOOGLE_PLACES_API_KEY

    # ------------------------------------------------------------------ Derived helpers
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def places_api_key(self) -> Optional[str]:
        return self.GOOGLE_MAPS_API_KEY or self.GOOGLE_PLACES_API_KEY

    # Per-integration configuration flags (used by tools/health for graceful degradation).
    @property
    def gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def serpapi_configured(self) -> bool:
        return bool(self.SERPAPI_API_KEY)

    @property
    def places_configured(self) -> bool:
        return bool(self.places_api_key)

    @property
    def tavily_configured(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def elevenlabs_configured(self) -> bool:
        return bool(self.ELEVENLABS_API_KEY)

    @property
    def neo4j_configured(self) -> bool:
        return bool(self.NEO4J_PASSWORD)


# Global settings instance
settings = Settings()
