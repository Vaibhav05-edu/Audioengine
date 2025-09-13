"""
Configuration settings for the Audio Drama FX Engine
"""

import os
from typing import List, Optional

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "Audio Drama FX Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    database_url: str = "postgresql://app:app@localhost:5432/fx"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_celery_url: str = "redis://localhost:6379/1"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # File uploads
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "uploads"
    allowed_audio_formats: List[str] = [".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"]

    # Audio processing
    ffmpeg_path: str = "ffmpeg"
    temp_dir: str = "temp"

    # Cache
    cache_dir: str = "cache"
    alignment_cache_ttl: int = 86400 * 7  # 7 days

    # External APIs
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None

    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
