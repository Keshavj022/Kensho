"""
Configuration settings for Kensho application
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Kensho"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Azure AI Foundry
    AZURE_AI_PROJECT_CONNECTION_STRING: Optional[str] = None
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: Optional[str] = None
    AZURE_PROJECT_NAME: Optional[str] = None

    # Azure Speech Services
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: str = "eastus"

    # Azure Vision Services
    AZURE_VISION_KEY: Optional[str] = None
    AZURE_VISION_ENDPOINT: Optional[str] = None

    # Model Configuration
    DEFAULT_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # Azure OpenAI Configuration (for RAG embeddings)
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT_URL")
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Data Paths
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    USER_DATA_PATH: str = os.path.join(DATA_DIR, "user_data.json")
    RESTAURANT_DATA_PATH: str = os.path.join(DATA_DIR, "restaurant_data.json")

    # Vector Store Configuration
    VECTOR_STORE_TYPE: str = "azure"  # "azure" or "chromadb"
    CHROMADB_PATH: str = "./chromadb_data"

    # Agent Configuration
    AGENT_NAME: str = "RestaurantAgent"
    AGENT_DESCRIPTION: str = "An AI agent that provides personalized restaurant recommendations"
    AGENT_INSTRUCTIONS: str = """You are a helpful restaurant recommendation agent.
Your role is to:
1. Understand user preferences, dietary restrictions, and location
2. Provide personalized restaurant recommendations
3. Suggest specific dishes based on user preferences
4. Answer questions about restaurants, menus, and food
5. Respect dietary restrictions and allergies
6. Provide contextual information about restaurants

Always be friendly, helpful, and considerate of dietary needs."""

    # Neo4j Configuration
    NEO4J_URI: Optional[str] = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: Optional[str] = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: Optional[str] = os.getenv("NEO4J_PASSWORD")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-use-env-var")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External API Keys (optional - system works without them but with limited functionality)
    # Restaurant APIs
    GOOGLE_PLACES_API_KEY: Optional[str] = os.getenv("GOOGLE_PLACES_API_KEY")
    YELP_API_KEY: Optional[str] = os.getenv("YELP_API_KEY")
    GEOAPIFY_API_KEY: Optional[str] = os.getenv("GEOAPIFY_API_KEY")
    
    # Travel APIs
    AMADEUS_API_KEY: Optional[str] = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET: Optional[str] = os.getenv("AMADEUS_API_SECRET")
    
    # Web Search APIs
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
    AZURE_BING_SEARCH_KEY: Optional[str] = os.getenv("AZURE_BING_SEARCH_KEY")
    AZURE_BING_SEARCH_ENDPOINT: Optional[str] = os.getenv("AZURE_BING_SEARCH_ENDPOINT")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
