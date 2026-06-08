from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # App
    app_env: Literal["development", "production"] = "development"
    secret_key: str = "dev-secret-change-in-prod"
    api_cors_origins: list[str] = ["http://localhost:5173"]

    # LLM
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: Literal["anthropic", "openai", "gemini"] = "gemini"
    llm_model: str = "gemini-2.0-pro"  # for Google GenAI, e.g. "gemini-1.5-pro", "gemini-2.0-pro", "gemini-2.5-pro"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_session_ttl: int = 86400

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "omnicx_kb"

    # ML
    sentiment_model_path: str = "ml/sentiment/model"
    churn_model_path: str = "ml/churn/model.pkl"
    sentiment_threshold: float = 0.75

    # Metrics
    metrics_flush_interval: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
