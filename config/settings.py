from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "RAG Query API"
    api_description: str = "API for querying documentation using RAG (Retrieval Augmented Generation)"
    api_version: str = "1.0.0"
    debug: bool = False

    # Qdrant Configuration - using the variables from your .env file
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")  # fallback
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))  # fallback
    qdrant_https: bool = os.getenv("QDRANT_HTTPS", "False").lower() == "true"  # fallback

    # AI Provider Configuration - using the variables from your .env file
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Collection name
    collection_name: str = os.getenv("COLLECTION_NAME", "rag_embedding")

    # Security Configuration
    api_key: str = os.getenv("API_KEY", "your-secure-api-key")  # fallback
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))  # fallback

    # Application Configuration
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")  # fallback

    class Config:
        env_file = ".env"
        # Allow extra fields to avoid validation errors
        extra = "allow"

settings = Settings()