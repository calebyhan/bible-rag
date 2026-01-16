"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra fields in .env for Docker Compose
    )

    # Database
    database_url: str = "postgresql://bible_user:bible_password@localhost:5432/bible_rag"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API Keys
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Embedding Model
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dimension: int = 1024

    # Cache
    cache_ttl: int = 86400  # 24 hours in seconds

    # Search
    max_results_default: int = 10
    vector_search_lists: int = 100
    similarity_threshold: float = 0.7

    # Server
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Rate Limiting
    gemini_rpm: int = 10  # Requests per minute
    groq_rpm: int = 30

    # Batch Processing
    enable_batching: bool = False  # Disabled - use direct Groq calls for reliability
    batch_window_ms: int = 500  # Wait time to accumulate requests
    max_batch_size: int = 10  # Maximum requests per batch


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
