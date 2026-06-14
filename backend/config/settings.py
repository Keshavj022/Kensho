"""Settings from environment / .env. Every external integration is optional — a
missing key disables that tool but the app still boots."""
from __future__ import annotations

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=(os.path.join(_REPO_ROOT, ".env"), os.path.join(_BACKEND_DIR, ".env")),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # tolerate stray legacy env vars without crashing
    )

    APP_NAME: str = "Kensho"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GEMINI_TEMPERATURE: float = 0.2

    OLLAMA_ENABLED: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"             # tool-capable model for agents/chat
    OLLAMA_VISION_MODEL: str = "llama3.2-vision"  # used for menu OCR fallback
    OLLAMA_TEMPERATURE: float = 0.2

    AZURE_OPENAI_ENDPOINT: Optional[str] = None      # https://<resource>.openai.azure.com/
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o-mini"      # tool-capable, multimodal (chat + menu OCR)
    AZURE_OPENAI_PRO_DEPLOYMENT: str = "gpt-4o"       # escalation for hard menu OCR
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"      # GA version supporting tools + vision
    AZURE_OPENAI_TEMPERATURE: float = 0.2
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Optional[str] = "text-embedding-3-small"

    AZURE_VISION_ENDPOINT: Optional[str] = None
    AZURE_VISION_KEY: Optional[str] = None

    AZURE_LANGUAGE_ENDPOINT: Optional[str] = None
    AZURE_LANGUAGE_KEY: Optional[str] = None

    AZURE_TRANSLATOR_ENDPOINT: str = "https://api.cognitive.microsofttranslator.com"
    AZURE_TRANSLATOR_KEY: Optional[str] = None
    AZURE_TRANSLATOR_REGION: Optional[str] = None

    GOOGLE_MAPS_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_GL: str = "in"  # country (in = India)
    SERPAPI_HL: str = "en"  # language
    SERPAPI_LOCATION: str = "India"
    DEFAULT_CURRENCY: str = "INR"

    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"  # default ElevenLabs voice
    ELEVENLABS_TTS_MODEL: str = "eleven_multilingual_v2"
    ELEVENLABS_STT_MODEL: str = "scribe_v2"
    ELEVENLABS_OUTPUT_FORMAT: str = "mp3_44100_128"
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    NEO4J_URI: Optional[str] = "bolt://localhost:7687"
    NEO4J_USERNAME: Optional[str] = "neo4j"
    NEO4J_PASSWORD: Optional[str] = None

    CHROMA_PATH: str = os.path.join(_REPO_ROOT, "chroma_data")
    EMBEDDING_DIM: int = 1536

    DATABASE_URL: str = "sqlite:///./kensho.db"
    CHECKPOINTER_DB_PATH: str = os.path.join(_REPO_ROOT, "kensho_checkpoints.db")
    SERVE_FRONTEND: bool = True

    JWT_SECRET_KEY: str = "dev-insecure-change-me"  # MUST be overridden in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MENU_CACHE_TTL_DAYS: int = 30
    SERPAPI_CACHE_TTL_HOURS: int = 6
    PLACES_CACHE_TTL_HOURS: int = 24

    DATA_DIR: str = os.path.join(_BACKEND_DIR, "data")
    USER_DATA_PATH: str = os.path.join(_BACKEND_DIR, "data", "user_data.json")
    RESTAURANT_DATA_PATH: str = os.path.join(_BACKEND_DIR, "data", "restaurant_data.json")
    CHROMADB_PATH: Optional[str] = None  # filled from CHROMA_PATH in __init__
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GOOGLE_PLACES_API_KEY: Optional[str] = None  # legacy name; falls back to GOOGLE_MAPS_API_KEY
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.isabs(self.CHROMA_PATH):
            self.CHROMA_PATH = os.path.abspath(os.path.join(_REPO_ROOT, self.CHROMA_PATH))
        if not self.CHROMADB_PATH:
            self.CHROMADB_PATH = self.CHROMA_PATH
        elif not os.path.isabs(self.CHROMADB_PATH):
            self.CHROMADB_PATH = os.path.abspath(os.path.join(_REPO_ROOT, self.CHROMADB_PATH))
        if not self.GOOGLE_MAPS_API_KEY and self.GOOGLE_PLACES_API_KEY:
            self.GOOGLE_MAPS_API_KEY = self.GOOGLE_PLACES_API_KEY

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def places_api_key(self) -> Optional[str]:
        return self.GOOGLE_MAPS_API_KEY or self.GOOGLE_PLACES_API_KEY

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgres")

    @property
    def pg_conninfo(self) -> str:
        """Raw libpq URL (strip any SQLAlchemy +driver) for psycopg / LangGraph saver."""
        url = self.DATABASE_URL
        return url.replace("postgresql+psycopg://", "postgresql://").replace(
            "postgresql+psycopg2://", "postgresql://"
        )

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

    @property
    def azure_openai_configured(self) -> bool:
        return bool(self.AZURE_OPENAI_API_KEY and self.AZURE_OPENAI_ENDPOINT)

    @property
    def azure_embeddings_configured(self) -> bool:
        return bool(self.azure_openai_configured and self.AZURE_OPENAI_EMBEDDING_DEPLOYMENT)

    @property
    def azure_vision_configured(self) -> bool:
        return bool(self.AZURE_VISION_KEY and self.AZURE_VISION_ENDPOINT)

    @property
    def azure_language_configured(self) -> bool:
        return bool(self.AZURE_LANGUAGE_KEY and self.AZURE_LANGUAGE_ENDPOINT)

    @property
    def azure_translator_configured(self) -> bool:
        return bool(self.AZURE_TRANSLATOR_KEY and self.AZURE_TRANSLATOR_REGION)


settings = Settings()
