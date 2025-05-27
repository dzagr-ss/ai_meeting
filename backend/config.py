from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meeting Transcription API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/meeting_transcription")
    
    # JWT
    SECRET_KEY: str = os.getenv("JWT_SECRET", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # Storage
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "storage")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]

    # Logging
    SHOW_BACKEND_LOGS: bool = os.getenv("SHOW_BACKEND_LOGS", "False").lower() in ("1", "true", "yes")

    class Config:
        case_sensitive = True

settings = Settings() 