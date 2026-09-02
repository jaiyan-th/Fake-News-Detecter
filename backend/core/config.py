"""
Application Configuration using Pydantic Settings
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App Info
    APP_NAME: str = "AI News Verification System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # API Keys
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API Key for LLM inference")
    NEWS_API_KEY: Optional[str] = Field(default=None, description="NewsAPI Key for real-time news retrieval")
    SERPAPI_KEY: Optional[str] = Field(default=None, description="SerpAPI Key for Google News search")


    # Embeddings
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5", description="FastEmbed model identifier")
    EMBEDDING_DIM: int = Field(default=384, description="Embedding vector dimensions")

    # Groq LLM Configuration
    GROQ_MODEL: str = Field(default="openai/gpt-oss-120b", description="Primary Groq model for speed and accuracy")
    GROQ_REASONING_MODEL: str = Field(default="openai/gpt-oss-20b", description="Secondary Groq model")
    GROQ_TIMEOUT_SECONDS: int = 25
    GROQ_MAX_RETRIES: int = 3

    # Search & Retrieval Limits
    NEWS_API_LIMIT: int = 15
    SERPAPI_LIMIT: int = 15
    REQUEST_TIMEOUT_SECONDS: int = 12
    TOP_K_EVIDENCE: int = 6
    EVIDENCE_FRESHNESS_DAYS: int = 60  # Prioritize within this window for breaking news

    # Authentication & Security
    JWT_SECRET_KEY: str = Field(default="dev-jwt-secret-key-replace-in-production-abcdef1234567890", description="HMAC Secret Key for JWT")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days session


settings = Settings()
