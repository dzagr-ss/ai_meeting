from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meeting Transcription API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database - Required, no default
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # JWT - Required, no insecure defaults
    SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key (minimum 32 characters)")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI - Required for transcription features
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key for transcription")
    
    # Gemini API - Required for AI features
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    
    # Email configuration - Required for password reset
    SMTP_SERVER: str = Field(..., description="SMTP server for email")
    SMTP_PORT: int = Field(587, description="SMTP port")
    SMTP_USERNAME: str = Field(..., description="SMTP username")
    SMTP_PASSWORD: str = Field(..., description="SMTP password")
    FROM_EMAIL: str = Field(..., description="From email address")
    
    # Storage
    STORAGE_PATH: str = Field(default="storage", description="File storage path")
    
    # CORS - Secure defaults
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000", 
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Frontend URL (optional)
    FRONTEND_URL: Optional[str] = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # Allowed hosts (optional)
    ALLOWED_HOSTS: Optional[str] = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts"
    )

    # Logging
    SHOW_BACKEND_LOGS: bool = Field(
        default=False, 
        description="Show detailed backend logs"
    )
    
    # Audio file management
    AUTO_CLEANUP_AUDIO_FILES: bool = Field(
        default=True,
        description="Automatically delete audio files after successful summarization"
    )
    
    # Database SSL configuration (optional)
    DB_SSL_CERT: Optional[str] = Field(default=None, description="Database SSL certificate path")
    DB_SSL_KEY: Optional[str] = Field(default=None, description="Database SSL key path")
    DB_SSL_ROOT_CERT: Optional[str] = Field(default=None, description="Database SSL root certificate path")

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        # Check for common insecure values
        insecure_keys = [
            'your-secret-key', 
            'your-secret-key-here', 
            'secret', 
            'password',
            'changeme'
        ]
        if v.lower() in insecure_keys:
            raise ValueError('SECRET_KEY cannot be a default or common value')
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite:///')):
            raise ValueError('DATABASE_URL must be a valid database connection string')
        return v
    
    @validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        if not v or not v.startswith('sk-'):
            raise ValueError('OPENAI_API_KEY must be a valid OpenAI API key')
        return v
    
    @validator('BACKEND_CORS_ORIGINS')
    def validate_cors_origins(cls, v):
        # Parse comma-separated origins
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        else:
            origins = v
        
        # Ensure no wildcard origins in production
        if '*' in origins:
            raise ValueError('Wildcard CORS origins are not allowed for security')
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables

# Generate a secure secret key if needed (for development setup)
def generate_secret_key() -> str:
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(32)

settings = Settings() 