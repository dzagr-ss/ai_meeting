# Compatible imports for both Pydantic v1 and v2
try:
    # Pydantic v2 import
    from pydantic_settings import BaseSettings
except ImportError:
    # Pydantic v1 fallback
    from pydantic import BaseSettings

from pydantic import Field, validator
from typing import Optional, List
import os
from dotenv import load_dotenv
import secrets

# Load .env file only if it exists (for local development)
if os.path.exists('.env'):
    load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meeting Transcription API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment detection
    ENVIRONMENT: str = Field(default="development", description="Environment: development, production")
    
    # Database - Required, no default
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # JWT - Generate secure default for production if not set
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32) if os.getenv("ENVIRONMENT") == "production" else "",
        min_length=32, 
        description="JWT secret key (minimum 32 characters)"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI - Optional in production to allow staged deployment
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, 
        description="OpenAI API key for transcription (required for full functionality)"
    )
    
    # Gemini API - Optional in production to allow staged deployment
    GEMINI_API_KEY: Optional[str] = Field(
        default=None, 
        description="Google Gemini API key (required for AI features)"
    )
    
    # Email configuration - Optional in production to allow staged deployment
    SMTP_SERVER: Optional[str] = Field(default="smtp.gmail.com", description="SMTP server for email")
    SMTP_PORT: int = Field(587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    FROM_EMAIL: Optional[str] = Field(default=None, description="From email address")
    
    # Storage - Use Railway volumes in production
    STORAGE_PATH: str = Field(default="/app/storage", description="File storage path")
    
    # CORS - Secure defaults with production environment support
    BACKEND_CORS_ORIGINS: str = Field(
        default="https://ai-meeting-indol.vercel.app,http://localhost:3000", 
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Frontend URL (optional) - Updated for production
    FRONTEND_URL: Optional[str] = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # Allowed hosts (optional) - Railway domains included
    ALLOWED_HOSTS: Optional[str] = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts"
    )

    # Logging - More verbose in development
    SHOW_BACKEND_LOGS: bool = Field(
        default=True, 
        description="Show detailed backend logs"
    )
    
    # Audio file management
    AUTO_CLEANUP_AUDIO_FILES: bool = Field(
        default=True,
        description="Automatically delete audio files after successful summarization"
    )
    
    # Database SSL configuration (optional) - Important for production
    DB_SSL_CERT: Optional[str] = Field(default=None, description="Database SSL certificate path")
    DB_SSL_KEY: Optional[str] = Field(default=None, description="Database SSL key path")
    DB_SSL_ROOT_CERT: Optional[str] = Field(default=None, description="Database SSL root certificate path")

    # Railway-specific settings
    PORT: int = Field(default=8000, description="Port to run the application on")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v:
            # Auto-generate in production if not provided
            if os.getenv("ENVIRONMENT") == "production":
                return secrets.token_urlsafe(32)
            else:
                raise ValueError('SECRET_KEY must be set in development')
        
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        
        # Check for common insecure values
        insecure_keys = [
            'your-secret-key', 
            'your-secret-key-here', 
            'secret', 
            'password',
            'changeme',
            'your-super-secret-jwt-key-min-32-characters-long-change-this-in-production'
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
        if v and not v.startswith('sk-'):
            raise ValueError('OPENAI_API_KEY must be a valid OpenAI API key starting with sk-')
        return v
    
    @validator('BACKEND_CORS_ORIGINS')
    def validate_cors_origins(cls, v):
        # Parse comma-separated origins
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        else:
            origins = v
        
        # Allow wildcard origins only in development
        environment = os.getenv('ENVIRONMENT', 'development')
        if '*' in origins and environment == 'production':
            raise ValueError('Wildcard CORS origins are not allowed in production')
        return v

    @validator('STORAGE_PATH')
    def validate_storage_path(cls, v):
        # Ensure storage directory exists
        os.makedirs(v, exist_ok=True)
        return v

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == 'development'
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == 'production'

    @property
    def has_openai_api(self) -> bool:
        """Check if OpenAI API is available"""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith('sk-'))
    
    @property 
    def has_gemini_api(self) -> bool:
        """Check if Gemini API is available"""
        return bool(self.GEMINI_API_KEY)
    
    @property
    def has_email_config(self) -> bool:
        """Check if email configuration is complete"""
        return bool(self.SMTP_USERNAME and self.SMTP_PASSWORD and self.FROM_EMAIL)

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables

# Generate a secure secret key if needed (for development setup)
def generate_secret_key() -> str:
    """Generate a cryptographically secure secret key"""
    return secrets.token_urlsafe(32)

settings = Settings() 