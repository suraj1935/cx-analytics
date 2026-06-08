"""Configuration and Settings"""

from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]
    
    # Audio
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    MAX_AUDIO_SIZE_MB: int = 50
    
    # Database (future)
    DATABASE_URL: str = "sqlite:///./data/evolvs.db"
    
    # JWT (future auth)
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
