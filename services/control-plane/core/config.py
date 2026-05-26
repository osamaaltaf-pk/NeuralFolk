import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuralFolk"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "database"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "neuralfolk"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@database:5432/neuralfolk"

    # Valkey
    VALKEY_HOST: str = "cache"
    VALKEY_PORT: int = 6379
    VALKEY_URL: str = "redis://cache:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://cache:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://cache:6379/0"

    # Qdrant
    QDRANT_HOST: str = "vector-db"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334

    # FalkorDB
    FALKORDB_HOST: str = "graph-db"
    FALKORDB_PORT: int = 6379

    # Ollama
    OLLAMA_HOST: str = "http://inference:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
