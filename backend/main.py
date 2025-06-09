import warnings
# Suppress all audio processing library warnings before importing them
warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", message="torchaudio._backend.set_audio_backend has been deprecated")
warnings.filterwarnings("ignore", message="torchaudio._backend.get_audio_backend has been deprecated")
warnings.filterwarnings("ignore", message="`torchaudio.backend.common.AudioMetaData` has been moved")
warnings.filterwarnings("ignore", message="Module 'speechbrain.pretrained' was deprecated")
import logging
import os
import sys
import time
import asyncio
import json
import base64
import tempfile
import shutil
import subprocess
import uuid
import hashlib
import secrets
import concurrent.futures
import glob
import mimetypes
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import re
from urllib.parse import quote
import psutil
import gc

# Suppress passlib bcrypt warning due to bcrypt 4.1+ compatibility issue
# See: https://github.com/pyca/bcrypt/issues/684
logging.getLogger('passlib').setLevel(logging.ERROR)

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request, Response, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, text, or_, and_
from passlib.context import CryptContext
from jose import JWTError, jwt
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis
from pydantic import BaseModel, EmailStr, validator
import openai
from openai import OpenAI

# Essential imports that should always work
import torch
import torchaudio
from pydub import AudioSegment
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import butter, filtfilt

# Optional imports with fallbacks for Railway deployment
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    print("⚠️  WhisperX not available - using fallback transcription")
    WHISPERX_AVAILABLE = False

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    print("⚠️  Noisereduce not available - audio will not be denoised")
    NOISEREDUCE_AVAILABLE = False

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Segment
    PYANNOTE_AVAILABLE = True
except ImportError:
    print("⚠️  PyAnnote.audio not available - using fallback speaker identification")
    PYANNOTE_AVAILABLE = False

# Optional Google GenerativeAI import
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
    print("✅  Google GenerativeAI loaded successfully")
except ImportError:
    print("⚠️  Google GenerativeAI not available - using OpenAI only")
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None
    GEMINI_AVAILABLE = False

# Import local modules
from database import get_db, engine, SessionLocal
import models
import schemas
import crud
from config import settings
from speaker_identification import create_speaker_identifier
from audio_processor import AudioChunker
from email_service import email_service

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Railway-specific constants
RAILWAY_MAX_FILE_SIZE_MB = 50  # Railway has upload limits
RAILWAY_MAX_PROCESSING_TIME_SECONDS = 300  # 5 minutes max
RAILWAY_STORAGE_PATH = "/app/storage"  # Railway volume path

# Try to import magic with fallback
MAGIC_AVAILABLE = False
magic = None

def get_magic_module():
    """Lazy import of magic module with proper error handling"""
    global magic, MAGIC_AVAILABLE
    if MAGIC_AVAILABLE:
        return magic
    
    try:
        import magic as magic_module
        magic = magic_module
        MAGIC_AVAILABLE = True
        print("python-magic library loaded successfully")
        return magic
    except ImportError as e:
        print(f"python-magic library not available: {e}")
        print("File type detection will use mimetypes fallback")
        MAGIC_AVAILABLE = False
        return None
    except Exception as e:
        print(f"Error loading python-magic: {e}")
        print("File type detection will use mimetypes fallback")
        MAGIC_AVAILABLE = False
        return None

async def validate_railway_limits(file: UploadFile):
    """Validate file size and type for Railway deployment"""
    if file.size > RAILWAY_MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {RAILWAY_MAX_FILE_SIZE_MB}MB"
        )
    
# Create specialized loggers
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log')
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)

audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - AUDIT - %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

app_logger = logging.getLogger('app')

def log_security_event(event_type: str, user_id: int = None, ip_address: str = None, details: dict = None):
    """Log security-related events"""
    event_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    security_logger.warning(json.dumps(event_data))

def log_audit_event(action: str, user_id: int, resource_type: str, resource_id: int = None, details: dict = None):
    """Log audit trail events"""
    event_data = {
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {}
    }
    audit_logger.info(json.dumps(event_data))

# Request logging middleware
# @app.middleware("http")  # COMMENTED OUT - MOVED AFTER APP CREATION
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Log request
    app_logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    app_logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
    
    # Log security events for suspicious activity
    if response.status_code == 401:
        log_security_event("unauthorized_access", ip_address=client_ip, details={
            "path": str(request.url.path),
            "method": request.method
        })
    elif response.status_code == 403:
        log_security_event("forbidden_access", ip_address=client_ip, details={
            "path": str(request.url.path),
            "method": request.method
        })
    elif response.status_code == 429:
        log_security_event("rate_limit_exceeded", ip_address=client_ip, details={
            "path": str(request.url.path),
            "method": request.method
        })
    
    return response

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meeting Transcription API",
    description="API for real-time meeting transcription and analysis",
    version="1.0.0"
)

# Record app start time for health check uptime calculation
app_start_time = time.time()

# Rate limiter setup with environment-aware limits
def get_rate_limit(dev_limit: str, prod_limit: str) -> str:
    """Get rate limit based on environment"""
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    return dev_limit if is_dev else prod_limit

# For development, use extremely high limits or disable rate limiting
is_development = os.getenv("ENVIRONMENT", "development") == "development"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100000/day", "10000/hour"] if is_development else ["1000/day", "100/hour"]
)
app.state.limiter = limiter

# Add SlowAPI middleware - this was missing!
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom rate limit handler with better error messages
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": getattr(exc, 'retry_after', None)
        }
    )
    response.headers["Retry-After"] = str(getattr(exc, 'retry_after', 60))
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' ws: wss:; "
        "media-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "speaker=()"
    )
    
    # Remove server information
    if "Server" in response.headers:
        del response.headers["Server"]
    
    return response

# CORS middleware with simple local development support
def get_allowed_origins():
    """Get allowed origins from settings with validation"""
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        try:
            # Use settings object instead of direct environment access
            origins_str = settings.BACKEND_CORS_ORIGINS
            print(f"[CORS] Raw origins string: {origins_str}")
            
            if origins_str:
                # Parse comma-separated origins (handle semicolons too)
                origins = []
                # Replace semicolons with commas and split, then clean up each origin
                normalized_str = origins_str.replace(';', ',').replace('\n', ',')
                
                for origin in normalized_str.split(","):
                    # Clean up the origin
                    origin = origin.strip().strip("'\"").rstrip(';,').strip()
                    
                    # Remove any non-printable characters
                    origin = ''.join(char for char in origin if char.isprintable())
                    
                    # Additional cleaning to remove any lingering semicolons or commas
                    while origin.endswith(';') or origin.endswith(','):
                        origin = origin.rstrip(';,').strip()
                    
                    if origin and (origin.startswith(("http://", "https://")) or origin == "*"):
                        origins.append(origin)
                        print(f"[CORS] Added origin: {origin}")
                
                if origins:
                    print(f"[CORS] Final origins: {origins}")
                    return origins
            
            # Default production origins if nothing valid found
            default_origins = [
                "https://ai-meeting-indol.vercel.app",
            ]
            print(f"[CORS] Using default production origins: {default_origins}")
            return default_origins
            
        except Exception as e:
            app_logger.error(f"Error parsing CORS origins: {e}")
            print(f"[CORS] Exception occurred: {e}")
            # Return safe defaults for production
            default_origins = [
                "https://ai-meeting-indol.vercel.app",
            ]
            print(f"[CORS] Using fallback production origins: {default_origins}")
            return default_origins
    else:
        # Development - allow all common local development origins
        dev_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]
        print(f"[CORS] Using development origins: {dev_origins}")
        return dev_origins

allowed_origins = get_allowed_origins()
app_logger.info(f"CORS allowed origins: {allowed_origins}")

# Environment detection
is_production = os.getenv("ENVIRONMENT", "development") == "production"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Enable credentials for local development
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Add more methods for development
    allow_headers=["*"] if not is_production else [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Cache-Control"
    ],  # Allow all headers in development, restrict in production
    expose_headers=["X-Total-Count"],  # Only expose necessary headers
    max_age=600 if is_production else 86400,  # Cache preflight for 10 min in prod, 24h in dev
)

# Security headers middleware
def get_allowed_hosts():
    """Get allowed hosts for TrustedHostMiddleware"""
    if not is_production:
        return ["*"]  # Allow all in development
    
    # In production, allow specific hosts
    allowed_hosts = [
        "aimeeting.up.railway.app",  # Railway domain
        "localhost",  # For health checks
        "127.0.0.1",  # For health checks
        "0.0.0.0",  # For health checks
        "::1",  # IPv6 localhost
        # Railway internal load balancer hosts
        "*.railway.app",  # Railway internal services
        "railway.app",  # Railway internal services
        "*.up.railway.app",  # Railway app domains
        # Allow any internal Railway IPs (these are health check sources)
        "100.64.0.2",  # Specific Railway health check IP from logs
    ]
    
    # Add any additional hosts from environment
    additional_hosts = os.getenv("ALLOWED_HOSTS", "")
    if additional_hosts:
        hosts = [host.strip() for host in additional_hosts.split(",") if host.strip()]
        allowed_hosts.extend(hosts)
    
    # For Railway health checks, be more permissive
    # Railway health checks may come from internal IPs without proper host headers
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    if railway_env:
        print(f"[RAILWAY] Detected Railway environment: {railway_env}")
        allowed_hosts.extend([
            "*",  # Temporarily allow all hosts to debug Railway health checks
        ])
    
    return allowed_hosts

allowed_hosts = get_allowed_hosts()
app_logger.info(f"Allowed hosts: {allowed_hosts}")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# Session middleware with secure configuration
session_secret = settings.SECRET_KEY
if not session_secret or len(session_secret) < 32:
    if is_production:
        raise ValueError("SECRET_KEY must be set and at least 32 characters long in production")
    else:
        session_secret = "dev-secret-key-not-for-production-use-only"

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    max_age=1800,  # 30 minutes
    same_site="strict",
    https_only=is_production
)

# CRITICAL: Health middleware added LAST so it's processed FIRST (FastAPI middleware is processed in reverse order)
# This ensures health endpoints completely bypass ALL middleware including TrustedHostMiddleware
@app.middleware("http")
async def health_first_middleware(request: Request, call_next):
    """
    CRITICAL: Health endpoint middleware that runs FIRST to bypass all other middleware.
    Must be added LAST to be processed FIRST due to FastAPI's reverse middleware order.
    """
    # Check for Railway environment
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"))
    
    # Debug logging for Railway health checks
    if request.url.path in ["/health", "/healthz", "/ready"]:
        print(f"[HEALTH] Railway Environment: {is_railway}")
        print(f"[HEALTH] Processing {request.url.path} request from {request.client}")
        print(f"[HEALTH] Request method: {request.method}")
        print(f"[HEALTH] Request URL: {request.url}")
        print(f"[HEALTH] Request headers: {dict(request.headers)}")
        
        try:
            # Create direct response without going through any other middleware
            if request.url.path == "/health":
                response_data = {"status": "ok"}
            elif request.url.path == "/healthz":
                response_data = {"status": "ok", "timestamp": time.time()}
            elif request.url.path == "/ready":
                response_data = {"status": "ready", "service": "stocks-agent-api"}
            
            print(f"[HEALTH] Returning response: {response_data}")
            response = JSONResponse(content=response_data, status_code=200)
            
            # Add headers for Railway compatibility
            response.headers["Content-Type"] = "application/json"
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
            # Add Railway-specific headers if detected
            if is_railway:
                response.headers["X-Railway-Health"] = "ok"
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
            
            print(f"[HEALTH] Response headers: {dict(response.headers)}")
            print(f"[HEALTH] Response status: {response.status_code}")
            print(f"[HEALTH] Response created successfully for {request.url.path}")
            return response
            
        except Exception as health_error:
            print(f"[HEALTH] Error in health middleware: {health_error}")
            print(f"[HEALTH] Error type: {type(health_error)}")
            import traceback
            print(f"[HEALTH] Error traceback: {traceback.format_exc()}")
            
            # Absolute fallback - return plain text
            fallback_response = PlainTextResponse(
                "OK", 
                status_code=200, 
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Type": "text/plain",
                    "X-Health-Fallback": "true"
                }
            )
            print(f"[HEALTH] Fallback response created")
            return fallback_response
    
    # For all other endpoints, continue with normal middleware processing
    print(f"[REQUEST] Non-health request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use settings object for API keys
GEMINI_API_KEY = settings.GEMINI_API_KEY

# Suppress Whisper FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", module="whisper.transcribe")

# Global cache for speaker identifier to avoid reloading models
_speaker_identifier_cache = None

def get_safe_email_for_path(email: str) -> str:
    """Convert email to a safe filename format"""
    return email.replace("@", "_at_").replace(".", "_").replace("/", "_").replace("\\", "_")

def get_cached_speaker_identifier():
    """Get a cached speaker identifier to avoid reloading heavy models"""
    global _speaker_identifier_cache
    if _speaker_identifier_cache is None:
        _speaker_identifier_cache = create_speaker_identifier()
    return _speaker_identifier_cache

def get_audio_file_hash(file_path: str) -> str:
    """Generate a hash for an audio file to enable caching"""
    try:
        with open(file_path, 'rb') as f:
            # Read first and last 1KB for quick hash (compromise between speed and uniqueness)
            start = f.read(1024)
            f.seek(-1024, 2)  # Seek to 1KB from end
            end = f.read(1024)
            file_size = os.path.getsize(file_path)
            
        content = start + end + str(file_size).encode()
        return hashlib.md5(content).hexdigest()
    except Exception:
        return hashlib.md5(file_path.encode()).hexdigest()

# Simple in-memory cache for processed audio files
_audio_processing_cache = {}

def process_single_audio_file(audio_file: str) -> List[dict]:
    """Process a single audio file with caching"""
    file_hash = get_audio_file_hash(audio_file)
    
    # Check cache first
    if file_hash in _audio_processing_cache:
        print(f"Using cached results for {os.path.basename(audio_file)}")
        return _audio_processing_cache[file_hash]
    
    try:
        print(f"Processing audio file for speaker analysis: {audio_file}")
        
        # Check if file exists and is readable
        if not os.path.exists(audio_file):
            print(f"Audio file does not exist: {audio_file}")
            return []
            
        # Check file size
        file_size = os.path.getsize(audio_file)
        if file_size == 0:
            print(f"Audio file is empty: {audio_file}")
            return []
            
        print(f"File size: {file_size} bytes")
        
        # Use cached speaker identifier
        speaker_identifier = get_cached_speaker_identifier()
        segments = speaker_identifier.process_audio(audio_file)
        
        # Add file-specific context
        filename = os.path.basename(audio_file)
        file_segments = []
        
        for segment in segments:
            refined_segment = segment.copy()
            refined_segment["source_file"] = filename
            file_segments.append(refined_segment)
        
        # Cache the results
        _audio_processing_cache[file_hash] = file_segments
        
        print(f"Extracted {len(file_segments)} segments from {filename}")
        return file_segments
        
    except Exception as e:
        print(f"Error processing audio file {audio_file}: {e}")
        if "Format not recognised" in str(e):
            print(f"Audio format issue with {audio_file}. This might be due to incorrect file format or corruption.")
        return []

async def perform_comprehensive_speaker_analysis(audio_files: List[str]) -> List[dict]:
    """
    Perform comprehensive speaker diarization on all audio files with optimizations
    Returns refined speaker segments with improved accuracy
    """
    if not audio_files:
        return []
    
    print(f"[SpeakerAnalysis] Starting speaker analysis for {len(audio_files)} audio files")
    
    # Limit the number of files to prevent excessive processing
    MAX_AUDIO_FILES = 10
    if len(audio_files) > MAX_AUDIO_FILES:
        print(f"[SpeakerAnalysis] Warning: Too many audio files ({len(audio_files)}), limiting to {MAX_AUDIO_FILES}")
        audio_files = audio_files[:MAX_AUDIO_FILES]
    
    # Process files in parallel for better performance
    max_workers = min(len(audio_files), 3)  # Limit to 3 workers to avoid overwhelming the system
    all_segments = []
    
    print(f"[SpeakerAnalysis] Processing files with {max_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks with timeout
        future_to_file = {}
        for audio_file in audio_files:
            future = executor.submit(process_single_audio_file, audio_file)
            future_to_file[future] = audio_file
        
        # Collect results as they complete with timeout
        completed_files = 0
        for future in concurrent.futures.as_completed(future_to_file, timeout=240):  # 4 minute timeout total
            audio_file = future_to_file[future]
            completed_files += 1
            
            try:
                print(f"[SpeakerAnalysis] Processing file {completed_files}/{len(audio_files)}: {os.path.basename(audio_file)}")
                file_segments = future.result(timeout=60)  # 1 minute timeout per file
                all_segments.extend(file_segments)
                print(f"[SpeakerAnalysis] File {completed_files} completed, got {len(file_segments)} segments")
            except concurrent.futures.TimeoutError:
                print(f"[SpeakerAnalysis] Timeout processing {audio_file}, skipping")
            except Exception as e:
                print(f"[SpeakerAnalysis] Error processing {audio_file}: {e}")
    
    print(f"[SpeakerAnalysis] Collected {len(all_segments)} total segments from all files")
    
    # Perform cross-file speaker clustering to improve consistency
    print(f"[SpeakerAnalysis] Starting speaker clustering...")
    refined_segments = cluster_speakers_across_files(all_segments)
    
    print(f"[SpeakerAnalysis] Comprehensive analysis complete: {len(refined_segments)} refined segments")
    return refined_segments

def cluster_speakers_across_files(segments: List[dict]) -> List[dict]:
    """
    Cluster speakers across multiple audio files to ensure consistent labeling
    """
    # Group segments by original speaker label
    speaker_groups = {}
    for segment in segments:
        speaker = segment["speaker"]
        if speaker not in speaker_groups:
            speaker_groups[speaker] = []
        speaker_groups[speaker].append(segment)
    
    # For now, use a simple mapping approach
    # In a more sophisticated implementation, you could use voice embeddings
    # to cluster speakers more accurately across files
    
    refined_segments = []
    speaker_mapping = {}
    next_speaker_id = 1
    
    for original_speaker, speaker_segments in speaker_groups.items():
        # Create a consistent speaker ID across all files
        if original_speaker not in speaker_mapping:
            speaker_mapping[original_speaker] = f"Speaker_{next_speaker_id}"
            next_speaker_id += 1
        
        consistent_speaker_id = speaker_mapping[original_speaker]
        
        # Update all segments with the consistent speaker ID
        for segment in speaker_segments:
            refined_segment = segment.copy()
            refined_segment["refined_speaker"] = consistent_speaker_id
            refined_segment["original_speaker"] = original_speaker
            refined_segments.append(refined_segment)
    
    # Sort segments by start time for chronological order
    refined_segments.sort(key=lambda x: x.get("start_time", 0))
    
    print(f"Speaker clustering complete: {len(speaker_mapping)} unique speakers identified")
    return refined_segments

async def update_transcriptions_with_refined_speakers(
    db: Session, 
    meeting_id: int, 
    refined_segments: List[dict]
) -> int:
    """
    Update existing transcriptions with refined speaker labels (optimized)
    """
    updated_count = 0
    
    try:
        print(f"[TranscriptionUpdate] Starting transcription updates for meeting {meeting_id}")
        
        # Get all existing transcriptions for this meeting
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        print(f"[TranscriptionUpdate] Found {len(transcriptions)} existing transcriptions to update")
        print(f"[TranscriptionUpdate] Found {len(refined_segments)} refined segments to match against")
        
        if not transcriptions or not refined_segments:
            print(f"[TranscriptionUpdate] No transcriptions or segments to process")
            return 0
        
        # Limit processing to prevent infinite loops
        MAX_TRANSCRIPTIONS = 1000
        MAX_SEGMENTS = 5000
        
        if len(transcriptions) > MAX_TRANSCRIPTIONS:
            print(f"[TranscriptionUpdate] Warning: Too many transcriptions ({len(transcriptions)}), limiting to {MAX_TRANSCRIPTIONS}")
            transcriptions = transcriptions[:MAX_TRANSCRIPTIONS]
        
        if len(refined_segments) > MAX_SEGMENTS:
            print(f"[TranscriptionUpdate] Warning: Too many segments ({len(refined_segments)}), limiting to {MAX_SEGMENTS}")
            refined_segments = refined_segments[:MAX_SEGMENTS]
        
        # Create an index of refined segments by text for faster lookup
        print(f"[TranscriptionUpdate] Creating segment index...")
        segment_text_index = {}
        for i, segment in enumerate(refined_segments):
            if i % 100 == 0:  # Progress indicator
                print(f"[TranscriptionUpdate] Indexing segment {i}/{len(refined_segments)}")
            
            text_key = segment.get("text", "").lower().strip()
            if text_key:
                if text_key not in segment_text_index:
                    segment_text_index[text_key] = []
                segment_text_index[text_key].append(segment)
        
        print(f"[TranscriptionUpdate] Created index with {len(segment_text_index)} unique text keys")
        
        # Batch update operations
        updates_to_apply = []
        
        # Create a mapping strategy based on text similarity and timing
        print(f"[TranscriptionUpdate] Finding matches for transcriptions...")
        for i, transcription in enumerate(transcriptions):
            if i % 50 == 0:  # Progress indicator
                print(f"[TranscriptionUpdate] Processing transcription {i}/{len(transcriptions)}")
            
            # Find the best matching refined segment (optimized)
            best_match = find_best_matching_segment_optimized(transcription, refined_segments, segment_text_index)
            
            if best_match and best_match.get("refined_speaker"):
                old_speaker = transcription.speaker
                new_speaker = best_match["refined_speaker"]
                
                if old_speaker != new_speaker:  # Only update if different
                    updates_to_apply.append({
                        'id': transcription.id,
                        'old_speaker': old_speaker,
                        'new_speaker': new_speaker
                    })
        
        print(f"[TranscriptionUpdate] Found {len(updates_to_apply)} transcriptions to update")
        
        # Apply bulk updates if any
        if updates_to_apply:
            # Limit batch size to prevent database issues
            BATCH_SIZE = 100
            
            for batch_start in range(0, len(updates_to_apply), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(updates_to_apply))
                batch = updates_to_apply[batch_start:batch_end]
                
                print(f"[TranscriptionUpdate] Processing batch {batch_start//BATCH_SIZE + 1}/{(len(updates_to_apply) + BATCH_SIZE - 1)//BATCH_SIZE}")
                
                # Use bulk update for better performance
                for update in batch:
                    db.query(models.Transcription).filter(
                        models.Transcription.id == update['id']
                    ).update({'speaker': update['new_speaker']})
                    updated_count += 1
                
                # Commit each batch
                db.commit()
                print(f"[TranscriptionUpdate] Committed batch, total updated: {updated_count}")
            
            print(f"[TranscriptionUpdate] Successfully updated {updated_count} transcriptions in total")
        else:
            print("[TranscriptionUpdate] No transcriptions needed updating")
        
    except Exception as e:
        print(f"[TranscriptionUpdate] Error updating transcriptions: {e}")
        db.rollback()
        raise e
    
    return updated_count

def find_best_matching_segment_optimized(
    transcription: models.Transcription, 
    refined_segments: List[dict],
    segment_text_index: dict
) -> dict:
    """
    Find the best matching refined segment for a given transcription (optimized)
    Uses text similarity and other heuristics with indexing for better performance
    """
    transcription_text = transcription.text.lower().strip()
    
    if not transcription_text:
        return None
    
    # First try exact match from index
    if transcription_text in segment_text_index:
        candidates = segment_text_index[transcription_text]
        if candidates:
            # If multiple exact matches, prefer one with similar speaker
            for candidate in candidates:
                if transcription.speaker in candidate.get("original_speaker", ""):
                    return candidate
            return candidates[0]  # Return first exact match
    
    # If no exact match, try fuzzy matching with a subset of segments
    best_match = None
    best_score = 0
    
    # Create word set for transcription for faster comparison
    transcription_words = set(transcription_text.split())
    
    # Limit the number of segments to check to prevent infinite loops
    MAX_SEGMENTS_TO_CHECK = 500
    segments_checked = 0
    
    # Only check segments that have at least one word in common
    for segment in refined_segments:
        # Safety check to prevent infinite loops
        segments_checked += 1
        if segments_checked > MAX_SEGMENTS_TO_CHECK:
            print(f"[SegmentMatching] Reached maximum segments to check ({MAX_SEGMENTS_TO_CHECK}), stopping search")
            break
        
        segment_text = segment.get("text", "").lower().strip()
        if not segment_text:
            continue
            
        segment_words = set(segment_text.split())
        
        # Quick check: if no common words, skip
        if not transcription_words.intersection(segment_words):
            continue
        
        # Calculate similarity score (optimized)
        similarity_score = calculate_text_similarity_optimized(transcription_words, segment_words)
        
        # Boost score if speakers are similar (for consistency)
        if transcription.speaker in segment.get("original_speaker", ""):
            similarity_score += 0.2
        
        if similarity_score > best_score and similarity_score > 0.3:  # Minimum threshold
            best_score = similarity_score
            best_match = segment
            
            # Early termination if we find a very good match
            if similarity_score > 0.9:
                break
    
    return best_match

def calculate_text_similarity_optimized(words1: set, words2: set) -> float:
    """Calculate text similarity using Jaccard similarity for optimization."""
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def migrate_existing_files(db: Session):
    """Migrate existing files from old structure to new user-based structure"""
    # This function can be called once to migrate existing files
    # Pattern: /tmp/meeting_{meeting_id}_{timestamp}.wav
    old_pattern = "/tmp/meeting_*.wav"
    old_files = glob.glob(old_pattern)
    
    migrated_count = 0
    failed_count = 0
    
    if old_files:
        print(f"Found {len(old_files)} files to migrate from old structure")
        
        for file_path in old_files:
            try:
                # Extract meeting_id from filename
                filename = os.path.basename(file_path)
                # Format: meeting_{meeting_id}_{timestamp}.wav
                parts = filename.replace('.wav', '').split('_')
                if len(parts) >= 3 and parts[0] == 'meeting':
                    meeting_id = int(parts[1])
                    
                    # Look up the meeting owner
                    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
                    if meeting and meeting.owner:
                        # Create new directory structure
                        safe_email = get_safe_email_for_path(meeting.owner.email)
                        new_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
                        os.makedirs(new_dir, exist_ok=True)
                        
                        # Move file to new location
                        new_path = os.path.join(new_dir, filename)
                        os.rename(file_path, new_path)
                        print(f"Migrated: {file_path} -> {new_path}")
                        migrated_count += 1
                    else:
                        print(f"Could not find meeting owner for file: {file_path}")
                        failed_count += 1
                else:
                    print(f"Could not parse meeting_id from filename: {filename}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error migrating file {file_path}: {e}")
                failed_count += 1
    
    return {"migrated": migrated_count, "failed": failed_count, "total": len(old_files)}
    
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if not crud.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@app.get("/")
async def root():
    return {"message": "Welcome to Meeting Transcription API"}

@app.post("/admin/migrate-files")
async def migrate_files_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Migrate existing files from old structure to new user-based structure"""
    # For security, you might want to add admin role checking here
    result = migrate_existing_files(db)
    return {
        "message": "File migration completed",
        "result": result
    }

@app.get("/admin/file-structure")
async def get_file_structure(
    current_user: models.User = Depends(get_current_user)
):
    """Get current file structure for debugging"""
    structure = {}
    
    # Check old structure
    old_files = glob.glob("/tmp/meeting_*.wav")
    structure["old_structure"] = [os.path.basename(f) for f in old_files]
    
    # Check new structure
    meetings_dir = "/tmp/meetings"
    structure["new_structure"] = {}
    
    if os.path.exists(meetings_dir):
        for user_dir in os.listdir(meetings_dir):
            user_path = os.path.join(meetings_dir, user_dir)
            if os.path.isdir(user_path):
                structure["new_structure"][user_dir] = {}
                for meeting_dir in os.listdir(user_path):
                    meeting_path = os.path.join(user_path, meeting_dir)
                    if os.path.isdir(meeting_path):
                        files = [f for f in os.listdir(meeting_path) if f.endswith('.wav')]
                        structure["new_structure"][user_dir][meeting_dir] = files
    
    return structure

@app.post("/users/", response_model=schemas.User)
@limiter.limit("5/minute")
async def create_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Get client IP for logging
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        log_security_event("user_registration_attempt_duplicate", ip_address=client_ip, details={
            "email": user.email
        })
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = crud.create_user(db=db, user=user)
    log_audit_event("user_created", new_user.id, "user", new_user.id, {
        "email": user.email,
        "ip_address": client_ip
    })
    return new_user

@app.post("/token")
@limiter.limit("10/minute")
async def login(request: Request, user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Get client IP for logging
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    user = crud.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        log_security_event("login_failed", ip_address=client_ip, details={
            "email": user_data.email
        })
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Defensive check: if user_type is None, set it to NORMAL and update in database
    if user.user_type is None:
        from models import UserType
        user.user_type = UserType.TRIAL
        db.commit()
        db.refresh(user)
    
    access_token = crud.create_access_token(data={"sub": user.email, "user_type": user.user_type.value})
    log_audit_event("user_login", user.id, "authentication", details={
        "ip_address": client_ip
    })
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/password-reset/request")
@limiter.limit("3/minute")
async def request_password_reset(request: Request, reset_request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset token to be sent via email"""
    # Get client IP for logging
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Check if user exists
    user = crud.get_user_by_email(db, reset_request.email)
    if not user:
        log_security_event("password_reset_attempt_invalid_email", ip_address=client_ip, details={
            "email": reset_request.email
        })
        # Don't reveal if email exists or not for security
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent."}
    
    # Create reset token
    token = crud.create_password_reset_token(db, reset_request.email)
    
    # Send email
    email_sent = email_service.send_password_reset_email(reset_request.email, token)
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send password reset email")
    
    return {"message": "If the email exists, a password reset link has been sent."}

@app.post("/password-reset/confirm")
@limiter.limit("5/minute")
async def confirm_password_reset(request: Request, reset_confirm: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with token and set new password"""
    # Validate token and reset password
    success = crud.reset_password(db, reset_confirm.token, reset_confirm.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return {"message": "Password has been successfully reset"}

@app.post("/meetings/", response_model=schemas.Meeting)
@limiter.limit("20/minute")  # Meeting creation
def create_meeting(
    request: Request,
    meeting: schemas.MeetingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user can create meetings
    if not crud.can_create_meetings(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please contact an administrator to activate your account before creating meetings."
        )
    
    # Set default meeting title if not provided
    if not meeting.title:
        current_time = datetime.now()
        meeting.title = current_time.strftime("%Y-%m-%d %H:%M")
    
    return crud.create_meeting(db=db, meeting=meeting, user_id=current_user.id)

@app.get("/meetings/", response_model=List[schemas.Meeting])
@limiter.limit(get_rate_limit("10000/minute", "60/minute"))  # Read operations
def get_meetings(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meetings = crud.get_meetings(db, skip=skip, limit=limit, user_id=current_user.id)
    return meetings

@app.put("/meetings/{meeting_id}", response_model=schemas.Meeting)
@limiter.limit("30/minute")  # Update operations
def update_meeting(
    request: Request,
    meeting_id: int,
    meeting_update: schemas.MeetingUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_meeting = crud.update_meeting(db=db, meeting_id=meeting_id, meeting_update=meeting_update, user_id=current_user.id)
    if not updated_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found or you don't have permission to update it")
    return updated_meeting

@app.delete("/meetings/{meeting_id}")
@limiter.limit("10/minute")  # Delete operations
def delete_meeting(
    request: Request,
    meeting_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_meeting(db=db, meeting_id=meeting_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found or you don't have permission to delete it")
    return {"message": "Meeting deleted successfully"}

@app.get("/meetings/{meeting_id}/transcriptions", response_model=List[schemas.Transcription])
@limiter.limit(get_rate_limit("10000/minute", "60/minute"))  # Read operations
def get_meeting_transcriptions(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the meeting exists and belongs to the current user
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get all transcriptions for this meeting, ordered by timestamp
    transcriptions = db.query(models.Transcription).filter(
        models.Transcription.meeting_id == meeting_id
    ).order_by(models.Transcription.timestamp).all()
    
    return transcriptions

@app.options("/meetings/{meeting_id}/transcribe")
async def options_transcribe():
    # Use the same origins as the main CORS middleware
    allowed_origins = get_allowed_origins()
    # For simplicity, return the first allowed origin (or * if multiple)
    origin = allowed_origins[0] if len(allowed_origins) == 1 else "*"
    
    return {
        "headers": {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "false",
        }
    }

@app.post("/meetings/{meeting_id}/transcribe")
@limiter.limit("10/minute")  # Resource intensive operations
async def transcribe_meeting(
    request: Request,
    meeting_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        print(f"[Transcribe] Starting secure upload processing for meeting {meeting_id}")
        
        # Create user-specific directory structure
        safe_email = get_safe_email_for_path(current_user.email)
        user_meeting_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
        
        # Use secure file upload
        try:
            audio_filename = await save_uploaded_file_securely(audio, user_meeting_dir)
            print(f"[Transcribe] Audio file securely saved to: {audio_filename}")
            print(f"[Transcribe] File size: {os.path.getsize(audio_filename) if os.path.exists(audio_filename) else 'unknown'} bytes")
            print(f"[Transcribe] Directory contents: {os.listdir(user_meeting_dir) if os.path.exists(user_meeting_dir) else 'directory not found'}")
        except HTTPException:
            # Re-raise validation errors
            raise
        except Exception as e:
            print(f"[Transcribe] Error during secure file upload: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process uploaded file"
            )
        
        # Convert audio to proper WAV format for speaker diarization if needed
        try:
            print(f"[Transcribe] Converting audio format...")
            # Use pydub to convert the audio to proper WAV format
            audio_segment = AudioSegment.from_file(audio_filename)
            # Convert to mono, 16kHz for consistency
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
            
            # Create new filename for converted audio
            base_name = os.path.splitext(audio_filename)[0]
            converted_filename = f"{base_name}_converted.wav"
            audio_segment.export(converted_filename, format="wav")
            
            # Replace original with converted version
            os.remove(audio_filename)
            os.rename(converted_filename, audio_filename)
            print(f"[Transcribe] Audio converted and saved to: {audio_filename}")
        except Exception as e:
            print(f"[Transcribe] Error converting audio format: {e}")
            # Continue with original file if conversion fails
        
        # Create a placeholder transcription record so the system knows audio exists
        try:
            placeholder_transcription = models.Transcription(
                meeting_id=meeting_id,
                speaker="System",
                text=".",
                timestamp=datetime.utcnow()
            )
            db.add(placeholder_transcription)
            db.commit()
            print(f"[Transcribe] Created placeholder transcription record: {placeholder_transcription.id}")
        except Exception as e:
            print(f"[Transcribe] Error creating placeholder transcription: {e}")
            db.rollback()
            # Continue anyway - the audio file is still saved
        
        # Return success message
        return {
            "message": "Audio file uploaded successfully. Transcription will be available after speaker diarization during meeting summary generation.",
            "audio_saved": True,
            "whisper_transcription": "skipped",
            "placeholder_transcription_created": True
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[Transcribe] Unexpected error in transcribe_meeting: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during upload: {str(e)}"
        )

@app.post("/meetings/{meeting_id}/identify-speakers", response_model=schemas.SpeakerIdentificationResponse)
@limiter.limit("5/minute")  # Very resource intensive
async def identify_speakers(
    request: Request,
    meeting_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    temp_audio_path = None
    try:
        # Create a temporary directory for secure file processing
        temp_dir = tempfile.mkdtemp()
        
        # Use secure file upload to temporary directory
        temp_audio_path = await save_uploaded_file_securely(audio, temp_dir)
        
        # Initialize speaker identifier
        speaker_identifier = create_speaker_identifier()
        
        # Process the audio
        segments = speaker_identifier.process_audio(temp_audio_path)
        
        # Count unique speakers
        unique_speakers = len(set(segment["speaker"] for segment in segments))
        
        return {
            "segments": segments,
            "total_speakers": unique_speakers
        }
        
    except HTTPException:
        # Re-raise validation errors
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio for speaker identification: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
                # Also clean up the temporary directory
                temp_dir = os.path.dirname(temp_audio_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary files: {cleanup_error}")

@app.post("/meetings/{meeting_id}/refine-speakers")
@limiter.limit("5/minute")  # Very resource intensive
async def refine_speaker_diarization(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Refine speaker diarization using all audio files for the meeting
    and update existing transcriptions with improved speaker labels
    """
    import asyncio
    
    try:
        print(f"[SpeakerRefinement] Starting speaker refinement for meeting {meeting_id}")
        
        # Verify the meeting exists and belongs to the current user
        meeting = db.query(models.Meeting).filter(
            models.Meeting.id == meeting_id,
            models.Meeting.owner_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Get all audio files for this meeting
        print(f"[SpeakerRefinement] Getting audio files for meeting {meeting_id}")
        audio_files = get_meeting_audio_files(meeting_id, current_user.email)
        if not audio_files:
            # Enhanced debugging for missing audio files
            safe_email = get_safe_email_for_path(current_user.email)
            user_meeting_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
            print(f"[SpeakerRefinement] No audio files found in: {user_meeting_dir}")
            
            # Check if directory exists
            if os.path.exists(user_meeting_dir):
                files_in_dir = os.listdir(user_meeting_dir)
                print(f"[SpeakerRefinement] Directory exists but contains: {files_in_dir}")
            else:
                print(f"[SpeakerRefinement] Directory doesn't exist")
            
            # Check for transcriptions without audio files (fallback mode)
            transcriptions = db.query(models.Transcription).filter(
                models.Transcription.meeting_id == meeting_id
            ).order_by(models.Transcription.timestamp).all()
            
            if transcriptions:
                print(f"[SpeakerRefinement] Found {len(transcriptions)} transcriptions without audio files - using fallback mode")
                
                # Simple speaker consistency fix without audio
                updated_count = 0
                speaker_mapping = {}
                next_speaker_id = 1
                
                for transcription in transcriptions:
                    current_speaker = transcription.speaker or "Unknown"
                    
                    if current_speaker not in speaker_mapping:
                        if current_speaker == "Unknown" or current_speaker.startswith("SPEAKER_"):
                            speaker_mapping[current_speaker] = f"Speaker_{next_speaker_id}"
                            next_speaker_id += 1
                        else:
                            speaker_mapping[current_speaker] = current_speaker
                    
                    new_speaker = speaker_mapping[current_speaker]
                    
                    if transcription.speaker != new_speaker:
                        transcription.speaker = new_speaker
                        updated_count += 1
                
                if updated_count > 0:
                    db.commit()
                
                return {
                    "message": "Speaker refinement completed in fallback mode (no audio files found)",
                    "audio_files_processed": 0,
                    "transcriptions_updated": updated_count,
                    "refined_segments": len(transcriptions),
                    "speaker_mapping": speaker_mapping,
                    "mode": "fallback_without_audio",
                    "debug_info": {
                        "expected_directory": user_meeting_dir,
                        "directory_exists": os.path.exists(user_meeting_dir),
                        "files_in_directory": os.listdir(user_meeting_dir) if os.path.exists(user_meeting_dir) else []
                    }
                }
            else:
                print(f"[SpeakerRefinement] No transcriptions and no audio files found")
                return {
                    "message": "No audio files or transcriptions found for this meeting",
                    "audio_files_processed": 0,
                    "transcriptions_updated": 0,
                    "refined_segments": 0,
                    "mode": "no_data_found",
                    "debug_info": {
                        "expected_directory": user_meeting_dir,
                        "directory_exists": os.path.exists(user_meeting_dir),
                        "files_in_directory": os.listdir(user_meeting_dir) if os.path.exists(user_meeting_dir) else [],
                        "suggestion": "Please ensure audio is being recorded and uploaded during the meeting"
                    }
                }
        
        # For now, skip the comprehensive speaker analysis if it's taking too long
        # Instead, use a simplified approach that just assigns consistent speaker IDs
        print(f"[SpeakerRefinement] Using simplified speaker refinement approach...")
        
        try:
            # Get existing transcriptions
            transcriptions = db.query(models.Transcription).filter(
                models.Transcription.meeting_id == meeting_id
            ).order_by(models.Transcription.timestamp).all()
            
            if not transcriptions:
                print(f"[SpeakerRefinement] No transcriptions found for meeting {meeting_id}")
                return {
                    "message": "No transcriptions found to refine",
                    "audio_files_processed": len(audio_files),
                    "transcriptions_updated": 0,
                    "refined_segments": 0
                }
            
            # Simple speaker refinement: assign consistent speaker IDs based on existing patterns
            updated_count = 0
            speaker_mapping = {}
            next_speaker_id = 1
            
            print(f"[SpeakerRefinement] Processing {len(transcriptions)} transcriptions...")
            
            for transcription in transcriptions:
                current_speaker = transcription.speaker or "Unknown"
                
                # Create consistent speaker mapping
                if current_speaker not in speaker_mapping:
                    if current_speaker == "Unknown" or current_speaker.startswith("SPEAKER_"):
                        speaker_mapping[current_speaker] = f"Speaker_{next_speaker_id}"
                        next_speaker_id += 1
                    else:
                        speaker_mapping[current_speaker] = current_speaker
                
                new_speaker = speaker_mapping[current_speaker]
                
                # Update if different
                if transcription.speaker != new_speaker:
                    transcription.speaker = new_speaker
                    updated_count += 1
            
            # Commit all changes
            if updated_count > 0:
                db.commit()
                print(f"[SpeakerRefinement] Updated {updated_count} transcriptions with consistent speaker IDs")
            else:
                print(f"[SpeakerRefinement] No transcriptions needed updating")
            
            # Apply consecutive speaker phrase grouping optimization
            print(f"[SpeakerRefinement] Applying consecutive speaker phrase grouping...")
            
            # Get updated transcriptions (after speaker refinement)
            updated_transcriptions = db.query(models.Transcription).filter(
                models.Transcription.meeting_id == meeting_id
            ).order_by(models.Transcription.timestamp).all()
            
            # Group consecutive phrases from the same speaker
            grouped_transcriptions = group_consecutive_speaker_phrases(updated_transcriptions)
            
            print(f"[SpeakerRefinement] Grouped {len(updated_transcriptions)} transcriptions into {len(grouped_transcriptions)} speaker segments")
            
            # Apply grouped transcriptions to database
            if grouped_transcriptions:
                grouped_count = apply_grouped_transcriptions_to_db(db, meeting_id, grouped_transcriptions)
                print(f"[SpeakerRefinement] Successfully applied {grouped_count} grouped transcriptions")
            else:
                print(f"[SpeakerRefinement] No grouped transcriptions to apply")
                grouped_count = 0
            
            print(f"[SpeakerRefinement] Simplified speaker refinement completed successfully")
            return {
                "message": "Speaker diarization refined successfully with consecutive phrase grouping",
                "audio_files_processed": len(audio_files),
                "transcriptions_updated": updated_count,
                "original_segments": len(transcriptions),
                "grouped_segments": len(grouped_transcriptions),
                "final_transcription_count": grouped_count,
                "speaker_mapping": speaker_mapping,
                "optimization_applied": "consecutive_speaker_grouping"
            }
            
        except Exception as simple_error:
            print(f"[SpeakerRefinement] Error in simplified refinement: {simple_error}")
            db.rollback()
            raise simple_error
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[SpeakerRefinement] Error in speaker refinement: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speaker refinement failed: {str(e)}"
        )

@app.websocket("/ws/meetings/{meeting_id}/stream")
async def stream_audio(
    websocket: WebSocket,
    meeting_id: int,
    db: Session = Depends(get_db)
):
    chunker = AudioChunker()
    speaker_identifier = None
    last_processed_segment = None # Variable to hold the last processed segment for merging
    time_tolerance = 0.1 # seconds - Tolerance for merging consecutive segments

    try:
        await websocket.accept()
        
        # Wait for authentication message
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        
        if auth_data.get("type") != "auth" or not auth_data.get("token"):
            await websocket.close(code=1008, reason="Authentication required")
            return
            
        # Extract token from Bearer format
        token = auth_data["token"]
        if token.startswith("Bearer "):
            token = token[7:]  # Remove "Bearer " prefix
            
        # Verify token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if not email:
                await websocket.close(code=1008, reason="Invalid token: no email")
                return
                
            # Verify user exists and can create meetings/transcriptions
            user = crud.get_user_by_email(db, email=email)
            if user is None:
                await websocket.close(code=1008, reason="Invalid token: user not found")
                return
                
            # Check if user can create meetings/transcriptions
            if not crud.can_create_meetings(user):
                await websocket.close(code=1008, reason="Account pending approval")
                return

        except JWTError:
            await websocket.close(code=1008, reason="Invalid or expired token")
            return

        if settings.SHOW_BACKEND_LOGS:
            print(f"WebSocket connected and authenticated for meeting {meeting_id}")

        # Initialize speaker identifier after authentication
        try:
            speaker_identifier = create_speaker_identifier()
            if settings.SHOW_BACKEND_LOGS:
                print("Speaker identifier initialized")
        except Exception as init_error:
            print(f"Error initializing speaker identifier: {init_error}")
            await websocket.close(code=1011, reason=f"Failed to initialize speaker identifier: {str(init_error)}")
            return

        meeting_audio_time = 0.0  # Track total audio time since meeting start

        # Process incoming raw audio data (Float32Array bytes)
        while True:
            data = await websocket.receive_bytes()

            if isinstance(data, bytes):
                try:
                    buffer_size_before = len(chunker.buffer)
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[WebSocket] Received audio chunk: {len(data)} bytes. Chunker buffer size before: {buffer_size_before}")
                    recv_time = time.time()

                    if len(data) % 4 != 0:
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"Warning: Received byte data length ({len(data)}) is not a multiple of 4. Skipping processing for this chunk.")
                         continue

                    audio_chunk = np.frombuffer(data, dtype=np.float32)
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[WebSocket] Audio chunk shape: {audio_chunk.shape}, dtype: {audio_chunk.dtype}")

                    # Process the audio chunk with the chunker and then the speaker identifier
                    async for processed_chunk, chunk_start_time, chunk_end_time in chunker.process_audio_stream([audio_chunk]):
                         # Use meeting_audio_time as the absolute chunk start time
                         abs_chunk_start_time = meeting_audio_time
                         abs_chunk_end_time = abs_chunk_start_time + (chunk_end_time - chunk_start_time)
                         process_start = time.time()
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Processing chunk: start={abs_chunk_start_time:.2f}s, end={abs_chunk_end_time:.2f}s, current_time={process_start}, delay={process_start - recv_time:.3f}s")
                         buffer_size_after = len(chunker.buffer)
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Chunker buffer size after: {buffer_size_after}")

                         # Process audio chunk with speaker identifier (with safety checks)
                         try:
                             # Verify speaker_identifier is still in a valid state
                             if (speaker_identifier and 
                                 hasattr(speaker_identifier, "__dict__") and 
                                 hasattr(speaker_identifier, "process_audio_chunk")):
                                 
                                 newly_processed_segments = speaker_identifier.process_audio_chunk(
                                     processed_chunk,
                                     abs_chunk_start_time
                                 )
                             else:
                                 print("[WebSocket] Speaker identifier in invalid state, skipping processing")
                                 newly_processed_segments = []
                         except (AttributeError, TypeError, RuntimeError) as speaker_error:
                             print(f"[WebSocket] Speaker identifier introspection error: {speaker_error}")
                             newly_processed_segments = []
                         except Exception as general_speaker_error:
                             print(f"[WebSocket] General speaker identifier error: {general_speaker_error}")
                             newly_processed_segments = []
                         
                         process_end = time.time()
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] SpeakerIdentifier returned {len(newly_processed_segments)} segments. Processing time: {process_end - process_start:.3f}s")

                         finalized_segments = []
                         current_merged_segment = last_processed_segment

                         for segment in newly_processed_segments:
                              if current_merged_segment is None:
                                   current_merged_segment = segment
                              elif (segment["speaker"] == current_merged_segment["speaker"] and 
                                    segment["start_time"] - current_merged_segment["end_time"] <= time_tolerance):
                                   # Merge consecutive segments from the same speaker
                                   current_merged_segment["text"] += " " + segment["text"]
                                   current_merged_segment["end_time"] = segment["end_time"]
                              else:
                                   # Different speaker or time gap too large, finalize current segment
                                   finalized_segments.append(current_merged_segment)
                                   current_merged_segment = segment

                         last_processed_segment = current_merged_segment

                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Number of segments finalized in this chunk: {len(finalized_segments)}")
                         if finalized_segments:
                              if settings.SHOW_BACKEND_LOGS:
                                  print(f"[WebSocket] Sending {len(finalized_segments)} finalized segments via WebSocket.")
                              for final_segment in finalized_segments:
                                   if settings.SHOW_BACKEND_LOGS:
                                       print(f"[WebSocket] Sending segment: {final_segment}")
                                   
                                   # Save transcription to database
                                   try:
                                       transcription = models.Transcription(
                                           meeting_id=meeting_id,
                                           speaker=final_segment["speaker"],
                                           text=final_segment["text"],
                                           timestamp=datetime.utcnow()
                                       )
                                       db.add(transcription)
                                       db.commit()
                                       if settings.SHOW_BACKEND_LOGS:
                                           print(f"[WebSocket] Saved transcription to database: {transcription.id}")
                                   except Exception as e:
                                       if settings.SHOW_BACKEND_LOGS:
                                           print(f"[WebSocket] Error saving transcription to database: {e}")
                                       db.rollback()
                                   
                                   await websocket.send_json({
                                       "type": "transcription",
                                       "data": {
                                           "segments": [final_segment],
                                           "start_time": final_segment["start_time"],
                                           "end_time": final_segment["end_time"]
                                       }
                                   })
                              if settings.SHOW_BACKEND_LOGS:
                                  print("[WebSocket] Finished sending finalized segments for this chunk.")

                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Pending last_processed_segment for next chunk: {last_processed_segment}")

                         # Increment meeting_audio_time by the chunk duration
                         meeting_audio_time += (chunk_end_time - chunk_start_time)

                except Exception as e:
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[WebSocket] Error processing received raw audio data: {e}")

            # Handle other data types if necessary
            # elif isinstance(data, str):
            #    print(f"Received text message: {data}")

    except WebSocketDisconnect:
        print(f"WebSocket disconnected from meeting {meeting_id}")
        # If there's a pending last_processed_segment when disconnecting, send it
        if last_processed_segment is not None:
            if settings.SHOW_BACKEND_LOGS:
                print("Sending final pending segment on disconnect.")
            
            # Save final transcription to database
            try:
                transcription = models.Transcription(
                    meeting_id=meeting_id,
                    speaker=last_processed_segment["speaker"],
                    text=last_processed_segment["text"],
                    timestamp=datetime.utcnow()
                )
                db.add(transcription)
                db.commit()
                if settings.SHOW_BACKEND_LOGS:
                    print(f"[WebSocket] Saved final transcription to database: {transcription.id}")
            except Exception as e:
                if settings.SHOW_BACKEND_LOGS:
                    print(f"[WebSocket] Error saving final transcription to database: {e}")
                db.rollback()
            
            try:
                await websocket.send_json({
                    "type": "transcription",
                    "data": {
                        "segments": [last_processed_segment],
                        "start_time": last_processed_segment["start_time"],
                        "end_time": last_processed_segment["end_time"]
                    }
                })
            except Exception as e:
                print(f"Error sending final segment on disconnect: {e}")
        
        # Process and send any remaining buffered audio in speaker_identifier
        if speaker_identifier:
            try:
                # More comprehensive safety checks to prevent introspection errors
                if (hasattr(speaker_identifier, "__dict__") and 
                    hasattr(speaker_identifier, "audio_buffer") and 
                    hasattr(speaker_identifier, "buffer_start_time")):
                    
                    # Additional check to ensure the object is in a valid state
                    try:
                        buffer_length = len(speaker_identifier.audio_buffer)
                        if buffer_length > 0:
                            if settings.SHOW_BACKEND_LOGS:
                                print("Processing remaining audio buffer on disconnect.")
                            remaining_segments = speaker_identifier.process_audio_chunk(
                                speaker_identifier.audio_buffer,
                                speaker_identifier.buffer_start_time
                            )
                            if remaining_segments:
                                for segment in remaining_segments:
                                    # Save remaining transcription to database
                                    try:
                                        transcription = models.Transcription(
                                            meeting_id=meeting_id,
                                            speaker=segment["speaker"],
                                            text=segment["text"],
                                            timestamp=datetime.utcnow()
                                        )
                                        db.add(transcription)
                                        db.commit()
                                        if settings.SHOW_BACKEND_LOGS:
                                            print(f"[WebSocket] Saved remaining transcription to database: {transcription.id}")
                                    except Exception as e:
                                        if settings.SHOW_BACKEND_LOGS:
                                            print(f"[WebSocket] Error saving remaining transcription to database: {e}")
                                        db.rollback()
                                    
                                    try:
                                        await websocket.send_json({
                                            "type": "transcription",
                                            "data": {
                                                "segments": [segment],
                                                "start_time": segment["start_time"],
                                                "end_time": segment["end_time"]
                                            }
                                        })
                                    except Exception as e:
                                        print(f"Error sending remaining segment on disconnect: {e}")
                            
                            # Clear the buffer after processing
                            try:
                                if hasattr(speaker_identifier, "audio_buffer"):
                                    speaker_identifier.audio_buffer = np.array([], dtype=np.float32)
                            except Exception as clear_error:
                                print(f"Error clearing audio buffer: {clear_error}")
                    except (AttributeError, TypeError, RuntimeError) as attr_error:
                        print(f"[WebSocket] Speaker identifier object in invalid state during cleanup: {attr_error}")
                else:
                    print("[WebSocket] Speaker identifier missing required attributes, skipping buffer processing")
            except Exception as e:
                print(f"[WebSocket] Error during speaker identifier cleanup: {e}")
                # Don't re-raise, just log and continue cleanup

    except Exception as e:
        print(f"WebSocket error for meeting {meeting_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except Exception as close_error:
            print(f"Error closing WebSocket: {close_error}")
    finally:
        try:
            # Cleanup chunker
            if chunker and hasattr(chunker, 'cleanup'):
                chunker.cleanup()
                if settings.SHOW_BACKEND_LOGS:
                    print("Cleaned up chunker resources")
        except Exception as cleanup_error:
            if settings.SHOW_BACKEND_LOGS:
                print(f"Error during chunker cleanup: {cleanup_error}")
        
        try:
            # Cleanup speaker_identifier with comprehensive error handling
            if speaker_identifier:
                try:
                    # Check if the object is in a valid state before cleanup
                    if hasattr(speaker_identifier, "__dict__"):
                        # Try to access a simple attribute to test object validity
                        _ = getattr(speaker_identifier, "sample_rate", None)
                        
                        # If we get here, the object seems valid, try cleanup
                        if hasattr(speaker_identifier, "audio_buffer"):
                            try:
                                speaker_identifier.audio_buffer = np.array([], dtype=np.float32)
                            except Exception:
                                pass  # Ignore cleanup errors
                        
                        # Try to cleanup any PyTorch/CUDA resources
                        if hasattr(speaker_identifier, "pipeline"):
                            try:
                                del speaker_identifier.pipeline
                            except Exception:
                                pass
                        
                        if hasattr(speaker_identifier, "whisper_model"):
                            try:
                                del speaker_identifier.whisper_model
                            except Exception:
                                pass
                        
                        if settings.SHOW_BACKEND_LOGS:
                            print("Cleaned up speaker identifier resources")
                    else:
                        print("Speaker identifier object in invalid state, skipping cleanup")
                        
                except (AttributeError, TypeError, RuntimeError) as introspection_error:
                    print(f"Introspection error during speaker identifier cleanup: {introspection_error}")
                except Exception as general_cleanup_error:
                    print(f"General error during speaker identifier cleanup: {general_cleanup_error}")
        except Exception as final_cleanup_error:
            print(f"Final cleanup error: {final_cleanup_error}")
        
        # Force garbage collection to help with memory cleanup
        try:
            import gc
            gc.collect()
        except Exception:
            pass

@app.post("/api/summarize-audio/")
@limiter.limit("3/minute")  # AI processing intensive
async def summarize_audio(request: Request, audio: UploadFile = File(...)):
    # TODO: Save file, run Gemini summary, etc.
    summary = "This is a dummy summary."  # Replace with real logic
    return JSONResponse({"summary": summary})

@app.get("/meetings/{meeting_id}/summaries", response_model=List[schemas.Summary])
@limiter.limit(get_rate_limit("5000/minute", "30/minute"))  # Read operations
def get_meeting_summaries(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the meeting exists and belongs to the current user
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get all summaries for this meeting, ordered by generation time (newest first)
    summaries = crud.get_meeting_summaries(db, meeting_id)
    return summaries

@app.get("/meetings/{meeting_id}/notes", response_model=List[schemas.MeetingNotes])
@limiter.limit(get_rate_limit("5000/minute", "30/minute"))  # Read operations
def get_meeting_notes_endpoint(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the meeting exists and belongs to the current user
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get all meeting notes for this meeting, ordered by generation time (newest first)
    meeting_notes = crud.get_meeting_notes(db, meeting_id)
    return meeting_notes

@app.get("/meetings/{meeting_id}/status")
@limiter.limit(get_rate_limit("10000/minute", "60/minute"))  # Status checks
def get_meeting_status_endpoint(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the meeting status
    status_info = crud.get_meeting_status(db, meeting_id, current_user.id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return status_info

@app.post("/meetings/{meeting_id}/end")
@limiter.limit("20/minute")  # Meeting operations
def end_meeting_endpoint(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Mark the meeting as ended
    updated_meeting = crud.mark_meeting_as_ended(db, meeting_id, current_user.id)
    
    if not updated_meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return {
        "message": "Meeting marked as ended successfully",
        "meeting_id": meeting_id,
        "end_time": updated_meeting.end_time,
        "status": updated_meeting.status
    }

@app.get("/api/meeting/{meeting_id}/summary")
@limiter.limit("10/minute")  # AI processing intensive
async def get_meeting_summary(
    request: Request,
    meeting_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify the meeting exists and belongs to the current user
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if there's already a stored summary
    stored_summary = crud.get_latest_meeting_summary(db, meeting_id)
    stored_meeting_notes = crud.get_latest_meeting_notes(db, meeting_id)
    
    if stored_summary and stored_meeting_notes:
        try:
            # Try to parse as JSON (new structured format)
            parsed_content = json.loads(stored_summary.content)
            if isinstance(parsed_content, dict) and ("summary" in parsed_content or "meeting_notes" in parsed_content):
                # Use stored meeting notes content
                response_data = {
                    "summary": parsed_content.get("summary", stored_summary.content),
                    "meeting_notes": stored_meeting_notes.content,
                    "action_items": parsed_content.get("action_items", "No action items identified.")
                }
                
                # Check if action items need to be regenerated with ChatGPT
                if (response_data.get("action_items") == "Action items will be generated using ChatGPT..." or 
                    not response_data.get("action_items") or 
                    response_data.get("action_items") == "No action items identified."):
                    
                    # Generate action items using ChatGPT
                    chatgpt_action_items = await generate_action_items_with_chatgpt(meeting_id, db)
                    response_data["action_items"] = chatgpt_action_items
                    
                    # Update the stored summary with new action items
                    parsed_content["action_items"] = chatgpt_action_items
                    summary_create = schemas.SummaryCreate(
                        meeting_id=meeting_id,
                        content=json.dumps(parsed_content)
                    )
                    crud.create_summary(db, summary_create)
                
                return response_data
            else:
                # Legacy format - return as summary only
                return {
                    "summary": stored_summary.content,
                    "meeting_notes": stored_meeting_notes.content if stored_meeting_notes else "No structured meeting notes available.",
                    "action_items": "No action items identified."
                }
        except (json.JSONDecodeError, TypeError):
            # Legacy format - return as summary only
            return {
                "summary": stored_summary.content,
                "meeting_notes": stored_meeting_notes.content if stored_meeting_notes else "No structured meeting notes available.",
                "action_items": "No action items identified."
            }
    
    # If no stored summary, generate a new one
    audio_files = get_meeting_audio_files(meeting_id, current_user.email)
    if not audio_files:
        # Enhanced debugging for missing audio files
        safe_email = get_safe_email_for_path(current_user.email)
        user_meeting_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
        print(f"[Summary] No audio files found in: {user_meeting_dir}")
        
        # Check if directory exists
        if os.path.exists(user_meeting_dir):
            files_in_dir = os.listdir(user_meeting_dir)
            print(f"[Summary] Directory exists but contains: {files_in_dir}")
        else:
            print(f"[Summary] Directory doesn't exist")
        
        # Check for existing transcriptions (fallback mode)
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        if transcriptions:
            print(f"[Summary] Found {len(transcriptions)} transcriptions without audio files - using fallback mode")
            
            # Generate summary from transcriptions only
            all_transcription_text = "\n".join([
                f"{t.speaker}: {t.text}" for t in transcriptions
            ])
            
            fallback_summary = {
                "summary": f"Meeting summary generated from {len(transcriptions)} transcription segments. Audio files were not available for enhanced processing.",
                "meeting_notes": all_transcription_text[:2000] + "..." if len(all_transcription_text) > 2000 else all_transcription_text,
                "action_items": "Action items could not be generated without audio files.",
                "debug_info": {
                    "mode": "fallback_from_transcriptions",
                    "transcription_count": len(transcriptions),
                    "expected_directory": user_meeting_dir,
                    "directory_exists": os.path.exists(user_meeting_dir),
                    "files_in_directory": os.listdir(user_meeting_dir) if os.path.exists(user_meeting_dir) else []
                }
            }
            
            return fallback_summary
        else:
            print(f"[Summary] No transcriptions and no audio files found")
            return JSONResponse({
                "summary": None, 
                "meeting_notes": None,
                "action_items": None,
                "error": "No audio files or transcriptions found for this meeting",
                "debug_info": {
                    "expected_directory": user_meeting_dir,
                    "directory_exists": os.path.exists(user_meeting_dir),
                    "files_in_directory": os.listdir(user_meeting_dir) if os.path.exists(user_meeting_dir) else [],
                    "suggestion": "Please ensure audio is being recorded and uploaded during the meeting"
                }
            }, status_code=404)
    try:
        # First, process any uploaded audio files that haven't been transcribed yet
        await process_uploaded_audio_files(meeting_id, audio_files, db)
        
        # Check if Gemini API key is available
        if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here":
            # Generate summary and meeting notes with Gemini
            structured_content = summarize_with_gemini_multiple_files(audio_files)
        else:
            print("[Summary] Gemini API key not configured, using OpenAI for summary generation")
            # Fallback to OpenAI for summary generation
            structured_content = await generate_summary_with_openai(meeting_id, db)
        
        # Generate action items with ChatGPT
        chatgpt_action_items = await generate_action_items_with_chatgpt(meeting_id, db)
        structured_content["action_items"] = chatgpt_action_items
        
        # Generate tags with ChatGPT
        generated_tags = await generate_tags_with_chatgpt(meeting_id, db)
        if generated_tags:
            # Add tags to the meeting
            crud.add_tags_to_meeting(db, meeting_id, generated_tags, current_user.id)
            print(f"[Summary] Generated and added tags: {generated_tags}")
        
        # Save the summary to database as JSON
        summary_create = schemas.SummaryCreate(
            meeting_id=meeting_id,
            content=json.dumps({
                "summary": structured_content["summary"],
                "action_items": structured_content["action_items"]
            })
        )
        crud.create_summary(db, summary_create)
        
        # Save the meeting notes separately
        if structured_content.get("meeting_notes"):
            meeting_notes_create = schemas.MeetingNotesCreate(
                meeting_id=meeting_id,
                content=structured_content["meeting_notes"]
            )
            crud.create_meeting_notes(db, meeting_notes_create)
        
        # Mark the meeting as ended
        crud.mark_meeting_as_ended(db, meeting_id, current_user.id)
        print(f"[Summary] Meeting {meeting_id} marked as ended")
        
        # Clean up audio files after successful summarization (if enabled)
        if settings.AUTO_CLEANUP_AUDIO_FILES:
            try:
                cleanup_stats = cleanup_meeting_audio_files(meeting_id, current_user.email)
                print(f"[Summary] Audio cleanup completed: {cleanup_stats}")
                
                # Add cleanup info to the response for debugging/monitoring
                structured_content["cleanup_stats"] = cleanup_stats
                
            except Exception as cleanup_error:
                print(f"[Summary] Audio cleanup failed (non-critical): {cleanup_error}")
                # Don't fail the entire summarization if cleanup fails
                structured_content["cleanup_stats"] = {"error": str(cleanup_error)}
        else:
            print(f"[Summary] Audio cleanup disabled by configuration")
            structured_content["cleanup_stats"] = {"disabled": True}
        
        return structured_content
    except Exception as e:
        return JSONResponse({
            "summary": None, 
            "meeting_notes": None,
            "action_items": None,
            "error": f"Error generating summary: {str(e)}"
        }, status_code=500)

def validate_and_fix_audio_file(file_path: str) -> bool:
    """
    Validate audio file and attempt to fix format issues
    Returns True if file is valid or was successfully fixed
    """
    try:
        # Try to load the file with pydub to check if it's valid
        audio_segment = AudioSegment.from_file(file_path)
        return True
    except Exception as e:
        print(f"Audio file validation failed for {file_path}: {e}")
        
        # If it's a format issue, try to detect and fix
        if "does not appear to be an audio format" in str(e) or "Format not recognised" in str(e):
            try:
                # Try to read as raw bytes and see if we can detect the format
                with open(file_path, 'rb') as f:
                    header = f.read(12)
                
                # Check for WebM signature
                if b'webm' in header.lower() or b'matroska' in header.lower():
                    print(f"Detected WebM format in {file_path}, attempting conversion...")
                    
                    # Create backup
                    backup_path = file_path + ".backup"
                    os.rename(file_path, backup_path)
                    
                    try:
                        # Convert WebM to WAV
                        audio_segment = AudioSegment.from_file(backup_path, format="webm")
                        audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
                        audio_segment.export(file_path, format="wav")
                        
                        # Remove backup if successful
                        os.remove(backup_path)
                        print(f"Successfully converted {file_path} from WebM to WAV")
                        return True
                        
                    except Exception as conv_e:
                        # Restore backup if conversion failed
                        os.rename(backup_path, file_path)
                        print(f"Failed to convert {file_path}: {conv_e}")
                        return False
                        
            except Exception as detect_e:
                print(f"Failed to detect format for {file_path}: {detect_e}")
                return False
        
        return False

def get_meeting_audio_files(meeting_id: int, user_email: str) -> List[str]:
    # Find all audio files for the given meeting_id and user
    safe_email = get_safe_email_for_path(user_email)
    user_meeting_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
    
    # Check new location first with multiple patterns and extensions
    patterns = [
        f"{user_meeting_dir}/meeting_{meeting_id}_*.wav",
        f"{user_meeting_dir}/meeting_{meeting_id}_*.webm",
        f"{user_meeting_dir}/recording_*.wav",
        f"{user_meeting_dir}/recording_*.webm",
        f"{user_meeting_dir}/*.wav",
        f"{user_meeting_dir}/*.webm",
        f"{user_meeting_dir}/*.mp3",
        f"{user_meeting_dir}/*.m4a",
        f"{user_meeting_dir}/*.flac",
        f"{user_meeting_dir}/*.ogg",
        f"{user_meeting_dir}/*.aac"
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    # Remove duplicates while preserving order
    files = list(dict.fromkeys(files))
    
    # If no files found in new location, check old location and migrate
    if not files:
        old_patterns = [
            f"/tmp/meeting_{meeting_id}_*.wav",
            f"/tmp/meeting_{meeting_id}_*.webm",
            f"/tmp/recording_{meeting_id}_*.wav",
            f"/tmp/recording_{meeting_id}_*.webm"
        ]
        
        old_files = []
        for pattern in old_patterns:
            old_files.extend(glob.glob(pattern))
        
        if old_files:
            # Create new directory and migrate files
            os.makedirs(user_meeting_dir, exist_ok=True)
            migrated_files = []
            
            for old_file in old_files:
                filename = os.path.basename(old_file)
                new_path = os.path.join(user_meeting_dir, filename)
                try:
                    os.rename(old_file, new_path)
                    migrated_files.append(new_path)
                    print(f"Auto-migrated: {old_file} -> {new_path}")
                except Exception as e:
                    print(f"Error auto-migrating file {old_file}: {e}")
            
            files = migrated_files
    
    # Validate and fix audio files
    valid_files = []
    for file_path in files:
        if validate_and_fix_audio_file(file_path):
            valid_files.append(file_path)
        else:
            print(f"Skipping invalid audio file: {file_path}")
    
    # Sort by timestamp (filename contains timestamp)
    valid_files.sort()
    print(f"[get_meeting_audio_files] Found {len(valid_files)} valid audio files for meeting {meeting_id}: {[os.path.basename(f) for f in valid_files]}")
    return valid_files

def summarize_with_gemini_multiple_files(audio_files: List[str]) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    
    # Combine all audio files into one summary
    combined_audio_data = []
    
    for audio_file in audio_files:
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
            combined_audio_data.append(audio_bytes)
    
    # For now, use the first file for summary (you could concatenate them)
    # TODO: Implement proper audio concatenation if needed
    if combined_audio_data:
        base64_audio = base64.b64encode(combined_audio_data[0]).decode("utf-8")
        
        # Detect the MIME type based on file extension
        first_file = audio_files[0]
        file_ext = os.path.splitext(first_file)[1].lower()
        
        mime_type_map = {
            '.wav': 'audio/wav',
            '.webm': 'audio/webm',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac'
        }
        
        mime_type = mime_type_map.get(file_ext, 'audio/wav')  # Default to wav
        print(f"[Gemini] Using MIME type {mime_type} for file {os.path.basename(first_file)}")
        
        # Initialize Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        
        # Prepare the prompt and content for structured output (without action items)
        file_list = ", ".join([f.split('/')[-1] for f in audio_files])
        prompt = f"""Analyze this meeting audio and provide a structured response with the following sections. Please respond in English only.

1. **SUMMARY**: A concise overview of the meeting's main points and outcomes
2. **MEETING NOTES**: Detailed notes covering key discussions, decisions, and important points mentioned

Please format your response exactly as follows:
SUMMARY:
[Your summary here]

MEETING NOTES:
[Your detailed notes here]

Files processed: {file_list}"""
        
        parts = [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": base64_audio}},
        ]
        
        # Call Gemini
        response = model.generate_content(parts)
        full_response = response.text or "No content generated."
        
        # Parse the structured response
        sections = {
            "summary": "",
            "meeting_notes": "",
            "action_items": ""  # Will be filled by ChatGPT
        }
        
        # Split the response into sections
        lines = full_response.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUMMARY:'):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = "summary"
                current_content = []
                # Add content after the colon if any
                content_after_colon = line[8:].strip()
                if content_after_colon:
                    current_content.append(content_after_colon)
            elif line.startswith('MEETING NOTES:'):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = "meeting_notes"
                current_content = []
                # Add content after the colon if any
                content_after_colon = line[14:].strip()
                if content_after_colon:
                    current_content.append(content_after_colon)
            elif current_section and line:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # If parsing failed, put everything in summary
        if not sections["summary"] and not sections["meeting_notes"]:
            sections["summary"] = full_response
            sections["meeting_notes"] = "No structured meeting notes available."
        
        # Set placeholder for action items (will be generated by ChatGPT later)
        sections["action_items"] = "Action items will be generated using ChatGPT..."
        
        return sections
    
    return {
        "summary": "No audio data found.",
        "meeting_notes": "No audio data found.",
        "action_items": "No audio data found."
    }

def summarize_with_gemini(wav_path: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    # Read the audio file and encode as base64
    with open(wav_path, "rb") as f:
        audio_bytes = f.read()
    base64_audio = base64.b64encode(audio_bytes).decode("utf-8")

    # Initialize Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

    # Prepare the prompt and content (use 'parts' with correct keys)
    prompt = "Summarize the main points and action items from this meeting audio. Please respond in English only."
    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": "audio/wav", "data": base64_audio}},
    ]

    # Call Gemini
    response = model.generate_content(parts)
    return response.text or "No summary generated."

async def generate_action_items_with_chatgpt(meeting_id: int, db: Session) -> str:
    """
    Generate action items using ChatGPT GPT-4o model based on meeting transcriptions.
    """
    try:
        # Check if OpenAI API key is available
        if not settings.OPENAI_API_KEY:
            return "OpenAI API key not configured. Cannot generate action items with ChatGPT."
        
        # Get all transcriptions for the meeting
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        if not transcriptions:
            return "No transcriptions available for action items generation."
        
        # Combine all transcription text into a single transcript
        full_transcript = ""
        for transcription in transcriptions:
            speaker = transcription.speaker or "Unknown"
            text = transcription.text or ""
            timestamp = transcription.timestamp.strftime("%H:%M:%S") if transcription.timestamp else "00:00:00"
            full_transcript += f"[{timestamp}] {speaker}: {text}\n"
        
        if not full_transcript.strip():
            return "No transcript content available for action items generation."
        
        # Initialize OpenAI client with explicit parameters only
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # Explicit timeout
                max_retries=2   # Explicit retry count
            )
        except TypeError:
            # Fallback for older OpenAI library versions
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Improved prompt for action items extraction
        prompt = """I will give you a meeting transcription. Please analyze it and prepare a comprehensive list of action items. Please respond in English only.

For each action item, please include:
- The specific task or action to be taken
- Who is responsible (if mentioned)
- Any deadlines or timeframes (if mentioned)
- Priority level (if apparent from context)

Format the response as a clear, organized list. If no action items are found, please state that clearly.

Here is the meeting transcription:"""
        
        # Call ChatGPT GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert meeting analyst specializing in extracting actionable items from meeting transcripts. You provide clear, organized, and comprehensive action item lists. Always respond in English only."
                },
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n{full_transcript}"
                }
            ],
            max_tokens=1500,
            temperature=0.3  # Lower temperature for more focused, consistent output
        )
        
        action_items = response.choices[0].message.content.strip()
        return action_items if action_items else "No action items identified from the meeting transcript."
        
    except Exception as e:
        print(f"Error generating action items with ChatGPT: {e}")
        return f"Error generating action items: {str(e)}"

async def generate_summary_with_openai(meeting_id: int, db: Session) -> dict:
    """
    Generate summary and meeting notes using OpenAI GPT-4o model based on meeting transcriptions.
    This is a fallback when Gemini API is not available.
    """
    try:
        # Check if OpenAI API key is available
        if not settings.OPENAI_API_KEY:
            return {
                "summary": "OpenAI API key not configured. Cannot generate summary.",
                "meeting_notes": "OpenAI API key not configured. Cannot generate meeting notes.",
                "action_items": ""
            }
        
        # Get all transcriptions for the meeting
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        if not transcriptions:
            return {
                "summary": "No transcriptions available for summary generation.",
                "meeting_notes": "No transcriptions available for meeting notes generation.",
                "action_items": ""
            }
        
        # Combine all transcription text into a single transcript
        full_transcript = ""
        for transcription in transcriptions:
            speaker = transcription.speaker or "Unknown"
            text = transcription.text or ""
            timestamp = transcription.timestamp.strftime("%H:%M:%S") if transcription.timestamp else "00:00:00"
            full_transcript += f"[{timestamp}] {speaker}: {text}\n"
        
        if not full_transcript.strip():
            return {
                "summary": "No transcript content available for summary generation.",
                "meeting_notes": "No transcript content available for meeting notes generation.",
                "action_items": ""
            }
        
        # Initialize OpenAI client with explicit parameters only
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # Explicit timeout
                max_retries=2   # Explicit retry count
            )
        except TypeError:
            # Fallback for older OpenAI library versions
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Generate summary
        summary_prompt = """I will give you a meeting transcription. Please analyze it and provide a concise summary of the main points and outcomes. Please respond in English only.

Focus on:
- Key topics discussed
- Important decisions made
- Main conclusions reached
- Overall meeting outcomes

Here is the meeting transcription:"""
        
        summary_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert meeting analyst specializing in creating concise, informative summaries of meeting content. Always respond in English only."
                },
                {
                    "role": "user", 
                    "content": f"{summary_prompt}\n\n{full_transcript}"
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        # Generate detailed meeting notes
        notes_prompt = """I will give you a meeting transcription. Please analyze it and provide detailed meeting notes covering key discussions, decisions, and important points mentioned. Please respond in English only.

Structure the notes with:
- Key discussion points
- Decisions made
- Important information shared
- Questions raised and answers provided
- Any concerns or issues discussed

Here is the meeting transcription:"""
        
        notes_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert meeting analyst specializing in creating comprehensive, well-structured meeting notes. Always respond in English only."
                },
                {
                    "role": "user", 
                    "content": f"{notes_prompt}\n\n{full_transcript}"
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        summary = summary_response.choices[0].message.content.strip()
        meeting_notes = notes_response.choices[0].message.content.strip()
        
        return {
            "summary": summary if summary else "No summary could be generated from the transcript.",
            "meeting_notes": meeting_notes if meeting_notes else "No meeting notes could be generated from the transcript.",
            "action_items": ""  # Will be filled by the action items function
        }
        
    except Exception as e:
        print(f"Error generating summary with OpenAI: {e}")
        return {
            "summary": f"Error generating summary: {str(e)}",
            "meeting_notes": f"Error generating meeting notes: {str(e)}",
            "action_items": ""
        }

async def process_uploaded_audio_files(meeting_id: int, audio_files: List[str], db: Session):
    """
    Process uploaded audio files with WhisperX for transcription and speaker diarization.
    This replaces placeholder transcriptions with actual WhisperX transcriptions with speaker labels.
    """
    try:
        print(f"[ProcessUpload] Processing uploaded audio files for meeting {meeting_id} with WhisperX")
        
        # Check if there are any placeholder transcriptions that need to be replaced
        placeholder_transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id,
            models.Transcription.speaker == "System",
            models.Transcription.text.like("Audio file uploaded:%")
        ).all()
        
        if not placeholder_transcriptions:
            print(f"[ProcessUpload] No placeholder transcriptions found for meeting {meeting_id}")
            return
        
        # Import WhisperX
        try:
            # Fix for PyTorch 2.6+ weights loading issue with WhisperX
            import torch
            
            # Monkey-patch torch.load to always use weights_only=False
            _original_torch_load = torch.load
            def patched_torch_load(*args, **kwargs):
                kwargs.setdefault('weights_only', False)
                return _original_torch_load(*args, **kwargs)
            torch.load = patched_torch_load
            
            import whisperx
            import gc
            
        except ImportError:
            print("[ProcessUpload] WhisperX not installed, falling back to OpenAI Whisper")
            # Fallback to original OpenAI Whisper implementation
            await process_uploaded_audio_files_fallback(meeting_id, audio_files, db)
            return
        
        # WhisperX configuration - can be configured via environment variables
        device = os.getenv("WHISPERX_DEVICE", "cpu")  # Use "cuda" if GPU is available
        batch_size = int(os.getenv("WHISPERX_BATCH_SIZE", "16"))  # Reduce if low on GPU memory
        compute_type = os.getenv("WHISPERX_COMPUTE_TYPE", "float32")  # Use "float16" for GPU
        model_size = os.getenv("WHISPERX_MODEL_SIZE", "base")  # base, small, medium, large
        
        print(f"[ProcessUpload] WhisperX config: device={device}, batch_size={batch_size}, compute_type={compute_type}, model_size={model_size}")
        
        # Process each audio file with WhisperX
        for audio_file in audio_files:
            try:
                print(f"[ProcessUpload] Processing audio file with WhisperX: {audio_file}")
                
                # 1. Load audio
                audio = whisperx.load_audio(audio_file)
                print(f"[ProcessUpload] Audio loaded, duration: {len(audio)/16000:.2f} seconds")
                
                # 2. Load WhisperX model for transcription
                model = whisperx.load_model(model_size, device, compute_type=compute_type)
                
                # 3. Transcribe with WhisperX with English language specified
                result = model.transcribe(audio, batch_size=batch_size, language="en")
                print(f"[ProcessUpload] Transcription completed, found {len(result.get('segments', []))} segments")
                
                # 4. Load alignment model and align whisper output
                try:
                    # Use English language code for alignment
                    model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
                    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
                    print(f"[ProcessUpload] Alignment completed")
                except Exception as align_error:
                    print(f"[ProcessUpload] Alignment failed: {align_error}")
                    print("[ProcessUpload] Continuing without alignment")
                    model_a = None
                
                # 5. Assign speaker labels with diarization
                diarize_model = None
                try:
                    # Check if HuggingFace token is available for diarization
                    hf_token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
                    
                    # Load diarization model - Updated for newer WhisperX versions
                    try:
                        # Try the newer import path first
                        diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=hf_token, device=device)
                    except AttributeError:
                        # Fallback to older import path
                        diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
                    
                    # Run diarization
                    diarize_segments = diarize_model(audio_file)
                    
                    # Assign speakers to transcription segments
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    print(f"[ProcessUpload] Speaker diarization completed")
                    
                except Exception as diarize_error:
                    print(f"[ProcessUpload] Speaker diarization failed: {diarize_error}")
                    if "pyannote" in str(diarize_error).lower():
                        print("[ProcessUpload] Hint: You may need to accept pyannote/speaker-diarization-3.1 user conditions at https://hf.co/pyannote/speaker-diarization-3.1")
                        print("[ProcessUpload] And set HUGGINGFACE_TOKEN environment variable")
                    elif "DiarizationPipeline" in str(diarize_error):
                        print("[ProcessUpload] Hint: WhisperX version compatibility issue. Try updating WhisperX or using a different version.")
                        print("[ProcessUpload] Alternative: pip install git+https://github.com/m-bain/whisperX.git")
                    print("[ProcessUpload] Continuing with transcription only (no speaker labels)")
                
                # 6. Process segments and create transcription records
                if result.get("segments"):
                    for i, segment in enumerate(result["segments"]):
                        try:
                            # Extract segment information
                            text = segment.get("text", "").strip()
                            start_time = segment.get("start", 0)
                            end_time = segment.get("end", 0)
                            
                            # Get speaker label (from diarization or default)
                            speaker = segment.get("speaker", f"Speaker_{(i % 3) + 1}")  # Cycle through Speaker_1, Speaker_2, Speaker_3
                            if not speaker or speaker == "None" or speaker == "SPEAKER_00":
                                speaker = f"Speaker_{(i % 3) + 1}"
                            
                            if text:  # Only create transcription if there's actual text
                                # Create a new transcription record
                                new_transcription = models.Transcription(
                                    meeting_id=meeting_id,
                                    speaker=speaker,
                                    text=text,
                                    timestamp=datetime.utcnow()
                                )
                                db.add(new_transcription)
                                print(f"[ProcessUpload] Added transcription: {speaker}: {text[:50]}...")
                        
                        except Exception as segment_error:
                            print(f"[ProcessUpload] Error processing segment: {segment_error}")
                            continue
                
                # Clean up models to free memory
                del model
                if model_a:
                    del model_a
                if diarize_model:
                    del diarize_model
                gc.collect()
                
            except Exception as e:
                print(f"[ProcessUpload] Error processing audio file {audio_file} with WhisperX: {e}")
                # Try fallback to OpenAI Whisper for this file
                try:
                    await process_single_file_fallback(audio_file, meeting_id, db)
                except Exception as fallback_error:
                    print(f"[ProcessUpload] Fallback also failed for {audio_file}: {fallback_error}")
                continue
        
        # Remove placeholder transcriptions
        for placeholder in placeholder_transcriptions:
            db.delete(placeholder)
        
        # Commit all changes
        db.commit()
        print(f"[ProcessUpload] Successfully processed {len(audio_files)} audio files with WhisperX")
        
    except Exception as e:
        print(f"[ProcessUpload] Error processing uploaded audio files with WhisperX: {e}")
        db.rollback()
        raise e

async def process_uploaded_audio_files_fallback(meeting_id: int, audio_files: List[str], db: Session):
    """
    Fallback function using OpenAI Whisper when WhisperX is not available.
    """
    try:
        print(f"[ProcessUpload] Using OpenAI Whisper fallback for meeting {meeting_id}")
        
        # Process each audio file with OpenAI Whisper
        for audio_file in audio_files:
            await process_single_file_fallback(audio_file, meeting_id, db)
        
        print(f"[ProcessUpload] Fallback processing completed for {len(audio_files)} files")
        
    except Exception as e:
        print(f"[ProcessUpload] Error in fallback processing: {e}")
        raise e

async def process_single_file_fallback(audio_file: str, meeting_id: int, db: Session):
    """
    Process a single audio file with OpenAI Whisper (fallback method).
    Handles large files by chunking them if they exceed the 25MB limit.
    """
    try:
        print(f"[ProcessUpload] Processing audio file with OpenAI Whisper: {audio_file}")
        
        # Check file size (OpenAI Whisper has a 25MB limit)
        file_size = os.path.getsize(audio_file)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        
        if file_size > max_size:
            print(f"[ProcessUpload] File size ({file_size} bytes) exceeds OpenAI limit ({max_size} bytes)")
            print(f"[ProcessUpload] Attempting to compress audio file...")
            
            # Try to compress the audio file
            try:
                from pydub import AudioSegment
                
                # Load and compress the audio
                audio_segment = AudioSegment.from_file(audio_file)
                
                # Reduce quality to fit within size limit
                # Try different compression levels
                compressed_file = audio_file.replace('.wav', '_compressed.wav')
                
                # Start with moderate compression
                audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
                
                # Export with lower bitrate
                audio_segment.export(compressed_file, format="wav", parameters=["-ac", "1", "-ar", "16000"])
                
                # Check if compressed file is small enough
                compressed_size = os.path.getsize(compressed_file)
                
                if compressed_size <= max_size:
                    print(f"[ProcessUpload] Successfully compressed file to {compressed_size} bytes")
                    audio_file = compressed_file
                else:
                    print(f"[ProcessUpload] Compression not sufficient ({compressed_size} bytes), skipping OpenAI processing")
                    # Create a placeholder transcription
                    transcription_text = f"Audio file too large for processing ({file_size} bytes). Please use a smaller file or enable WhisperX."
                    
                    new_transcription = models.Transcription(
                        meeting_id=meeting_id,
                        speaker="Speaker_1",
                        text=transcription_text,
                        timestamp=datetime.utcnow()
                    )
                    db.add(new_transcription)
                    print(f"[ProcessUpload] Added placeholder transcription for large file")
                    return
                    
            except Exception as compress_error:
                print(f"[ProcessUpload] Audio compression failed: {compress_error}")
                # Create a placeholder transcription
                transcription_text = f"Audio file too large for processing and compression failed. File size: {file_size} bytes."
                
                new_transcription = models.Transcription(
                    meeting_id=meeting_id,
                    speaker="Speaker_1", 
                    text=transcription_text,
                    timestamp=datetime.utcnow()
                )
                db.add(new_transcription)
                print(f"[ProcessUpload] Added placeholder transcription for unprocessable file")
                return
        
        # Use OpenAI Whisper to transcribe the audio with defensive client initialization
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # Explicit timeout
                max_retries=2   # Explicit retry count
            )
        except TypeError:
            # Fallback for older OpenAI library versions
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                language="en",  # Specify English language
                file=f,
                response_format="text"
            )
        
        transcription_text = transcript.strip() if transcript else ""
        
        if transcription_text:
            # Create a new transcription record
            new_transcription = models.Transcription(
                meeting_id=meeting_id,
                speaker="Speaker_1",  # Default speaker, will be refined later
                text=transcription_text,
                timestamp=datetime.utcnow()
            )
            db.add(new_transcription)
            print(f"[ProcessUpload] Added fallback transcription: {transcription_text[:50]}...")
        
        # Clean up compressed file if it was created
        if 'compressed_file' in locals() and os.path.exists(compressed_file) and compressed_file != audio_file:
            try:
                os.remove(compressed_file)
                print(f"[ProcessUpload] Cleaned up compressed file: {compressed_file}")
            except Exception as cleanup_error:
                print(f"[ProcessUpload] Error cleaning up compressed file: {cleanup_error}")
            
    except Exception as e:
        print(f"[ProcessUpload] Error processing audio file {audio_file} with OpenAI Whisper: {e}")
        raise e

def group_consecutive_speaker_phrases(transcriptions: List[models.Transcription]) -> List[Dict[str, Any]]:
    """
    Group consecutive phrases from the same speaker into single entries.
    Returns a list of grouped transcription data.
    """
    if not transcriptions:
        return []
    
    grouped_transcriptions = []
    current_group = None
    
    for transcription in transcriptions:
        speaker = transcription.speaker or "Unknown"
        text = transcription.text or ""
        timestamp = transcription.timestamp
        
        # Skip empty text
        if not text.strip():
            continue
        
        # If this is the first transcription or speaker changed, start a new group
        if current_group is None or current_group["speaker"] != speaker:
            # Save the previous group if it exists
            if current_group is not None:
                grouped_transcriptions.append(current_group)
            
            # Start a new group
            current_group = {
                "speaker": speaker,
                "text": text.strip(),
                "start_timestamp": timestamp,
                "end_timestamp": timestamp,
                "transcription_ids": [transcription.id]
            }
        else:
            # Same speaker, append to current group
            current_group["text"] += " " + text.strip()
            current_group["end_timestamp"] = timestamp
            current_group["transcription_ids"].append(transcription.id)
    
    # Don't forget the last group
    if current_group is not None:
        grouped_transcriptions.append(current_group)
    
    return grouped_transcriptions

def apply_grouped_transcriptions_to_db(db: Session, meeting_id: int, grouped_transcriptions: List[Dict[str, Any]]) -> int:
    """
    Apply grouped transcriptions to the database by removing old transcriptions 
    and creating new grouped ones.
    """
    try:
        # Delete all existing transcriptions for this meeting
        deleted_count = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).delete()
        
        print(f"[GroupTranscriptions] Deleted {deleted_count} original transcriptions")
        
        # Create new grouped transcriptions
        created_count = 0
        for group in grouped_transcriptions:
            new_transcription = models.Transcription(
                meeting_id=meeting_id,
                speaker=group["speaker"],
                text=group["text"],
                timestamp=group["start_timestamp"]  # Use the start timestamp of the group
            )
            db.add(new_transcription)
            created_count += 1
        
        # Commit all changes
        db.commit()
        print(f"[GroupTranscriptions] Created {created_count} grouped transcriptions")
        
        return created_count
        
    except Exception as e:
        print(f"[GroupTranscriptions] Error applying grouped transcriptions: {e}")
        db.rollback()
        raise e

@app.post("/meetings/{meeting_id}/group-transcriptions")
@limiter.limit("10/minute")  # Processing intensive
async def group_meeting_transcriptions(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Group consecutive phrases from the same speaker into single transcription entries.
    This optimization makes transcriptions more readable by combining fragmented speech.
    """
    try:
        print(f"[GroupTranscriptions] Starting transcription grouping for meeting {meeting_id}")
        
        # Verify the meeting exists and belongs to the current user
        meeting = db.query(models.Meeting).filter(
            models.Meeting.id == meeting_id,
            models.Meeting.owner_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Get all transcriptions for this meeting, ordered by timestamp
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        if not transcriptions:
            return {
                "message": "No transcriptions found to group",
                "original_count": 0,
                "grouped_count": 0,
                "optimization_applied": "consecutive_speaker_grouping"
            }
        
        original_count = len(transcriptions)
        print(f"[GroupTranscriptions] Found {original_count} transcriptions to group")
        
        # Group consecutive phrases from the same speaker
        grouped_transcriptions = group_consecutive_speaker_phrases(transcriptions)
        grouped_count = len(grouped_transcriptions)
        
        print(f"[GroupTranscriptions] Grouped {original_count} transcriptions into {grouped_count} speaker segments")
        
        # Apply grouped transcriptions to database
        if grouped_transcriptions:
            final_count = apply_grouped_transcriptions_to_db(db, meeting_id, grouped_transcriptions)
            print(f"[GroupTranscriptions] Successfully applied {final_count} grouped transcriptions")
        else:
            print(f"[GroupTranscriptions] No grouped transcriptions to apply")
            final_count = 0
        
        # Calculate reduction percentage
        reduction_percentage = ((original_count - grouped_count) / original_count * 100) if original_count > 0 else 0
        
        print(f"[GroupTranscriptions] Transcription grouping completed successfully")
        return {
            "message": "Transcriptions grouped successfully",
            "original_count": original_count,
            "grouped_count": grouped_count,
            "final_count": final_count,
            "reduction_percentage": round(reduction_percentage, 1),
            "optimization_applied": "consecutive_speaker_grouping"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[GroupTranscriptions] Error in transcription grouping: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription grouping failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Ultra-simple health check for Railway - bypasses all middleware"""
    return {"status": "ok"}

@app.get("/healthz")
async def health_check_detailed():
    """Detailed health check for Railway (alternative endpoint)"""
    return {"status": "ok", "timestamp": time.time()}

@app.get("/ready")
async def readiness_check():
    """Readiness check for Railway - alternative health endpoint"""
    return {"status": "ready", "service": "stocks-agent-api"}

@app.get("/metrics")
async def get_metrics():
    """System metrics for monitoring"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    
    return {
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        },
        "cpu_percent": cpu,
        "model_cache_size": len(_audio_processing_cache)
    }


# File upload security configuration
ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.webm'}
ALLOWED_AUDIO_MIMETYPES = {
    'audio/wav', 'audio/wave', 'audio/x-wav',
    'audio/mpeg', 'audio/mp3',
    'audio/mp4', 'audio/m4a',
    'audio/flac',
    'audio/ogg',
    'audio/aac',
    'audio/webm',
    'video/webm'  # WebM files are often detected as video even when audio-only
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILENAME_LENGTH = 255

def validate_audio_file(file: UploadFile) -> None:
    """Comprehensive audio file validation"""
    
    # Check filename length
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename too long"
        )
    
    # Check for dangerous characters in filename
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
    if any(char in file.filename for char in dangerous_chars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )
    
    # Check content type
    if file.content_type not in ALLOWED_AUDIO_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type for audio file"
        )

def validate_file_content(file_path: str) -> None:
    """Validate file content using magic numbers"""
    try:
        # Use python-magic to detect actual file type
        file_type = magic.from_file(file_path, mime=True)
        print(f"[FileValidation] Magic detected file type: {file_type} for file: {file_path}")
        
        if file_type not in ALLOWED_AUDIO_MIMETYPES:
            # Special handling for WebM files that might be detected differently
            if 'webm' in file_type.lower() or file_type == 'video/webm':
                print(f"[FileValidation] WebM file detected as {file_type}, allowing it")
                return  # Allow WebM files even if detected as video/webm
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match expected audio format. Detected: {file_type}"
            )
    except Exception as e:
        print(f"[FileValidation] Magic detection failed: {e}")
        # If magic fails, try with mimetypes as fallback
        guessed_type, _ = mimetypes.guess_type(file_path)
        print(f"[FileValidation] Mimetypes guessed: {guessed_type} for file: {file_path}")
        
        # Check if it's a webm file by extension
        if file_path.lower().endswith('.webm'):
            print(f"[FileValidation] File has .webm extension, allowing it")
            return  # Allow .webm files
        
        if guessed_type not in ALLOWED_AUDIO_MIMETYPES:
            # More lenient fallback - if it's any audio type, allow it
            if guessed_type and guessed_type.startswith('audio/'):
                print(f"[FileValidation] Allowing audio file with type: {guessed_type}")
                return
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to verify file type"
            )

def secure_filename(filename: str) -> str:
    """Generate a secure filename"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[:MAX_FILENAME_LENGTH - len(ext)] + ext
    
    # Add timestamp to prevent conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    return f"{name}_{timestamp}{ext}"

async def save_uploaded_file_securely(file: UploadFile, destination_dir: str) -> str:
    """Securely save uploaded file with validation"""
    
    # Validate file before processing
    validate_audio_file(file)
    
    # Create secure filename
    secure_name = secure_filename(file.filename)
    file_path = os.path.join(destination_dir, secure_name)
    
    # Ensure destination directory exists
    os.makedirs(destination_dir, exist_ok=True)
    
    # Read file content with size limit
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Validate file content after saving
    validate_file_content(file_path)
    
    return file_path

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent information disclosure"""
    
    # Log the full error for debugging
    app_logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Log security event for potential attacks
    log_security_event("unhandled_exception", details={
        "path": str(request.url.path),
        "method": request.method,
        "error_type": type(exc).__name__
    })
    
    # Return generic error message to prevent information disclosure
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "error_id": str(uuid.uuid4())  # Unique error ID for tracking
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    
    # Log HTTP exceptions
    if exc.status_code >= 500:
        app_logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    elif exc.status_code >= 400:
        app_logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    
    # Log security events for certain status codes
    if exc.status_code in [401, 403, 404]:
        log_security_event(f"http_{exc.status_code}", details={
            "path": str(request.url.path),
            "method": request.method,
            "detail": exc.detail
        })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    app_logger.warning(f"Validation error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "detail": str(exc)
        }
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    """Handle permission errors"""
    app_logger.warning(f"Permission error: {str(exc)}")
    
    log_security_event("permission_denied", details={
        "path": str(request.url.path),
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Permission denied",
            "detail": "You don't have permission to access this resource"
        }
    )

# Tag endpoints
@app.post("/tags/", response_model=schemas.Tag)
@limiter.limit("30/minute")  # Tag creation
def create_tag(
    request: Request,
    tag: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_tag(db=db, tag=tag)

@app.get("/tags/", response_model=List[schemas.Tag])
@limiter.limit(get_rate_limit("10000/minute", "60/minute"))  # Read operations
def get_tags(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_tags(db=db, skip=skip, limit=limit)

@app.get("/tags/{tag_id}", response_model=schemas.Tag)
@limiter.limit("60/minute")  # Read operations
def get_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tag = crud.get_tag(db=db, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

@app.put("/tags/{tag_id}", response_model=schemas.Tag)
@limiter.limit("30/minute")  # Update operations
def update_tag(
    request: Request,
    tag_id: int,
    tag_update: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    tag = crud.update_tag(db=db, tag_id=tag_id, tag_update=tag_update)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

@app.delete("/tags/{tag_id}")
@limiter.limit("30/minute")  # Delete operations
def delete_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    success = crud.delete_tag(db=db, tag_id=tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return {"message": "Tag deleted successfully"}

@app.post("/meetings/{meeting_id}/tags")
@limiter.limit("30/minute")  # Tag operations
def add_tags_to_meeting(
    request: Request,
    meeting_id: int,
    tag_names: List[str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    meeting = crud.add_tags_to_meeting(
        db=db, 
        meeting_id=meeting_id, 
        tag_names=tag_names, 
        user_id=current_user.id
    )
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    return {"message": "Tags added successfully", "tags": [tag.name for tag in meeting.tags]}

@app.post("/meetings/{meeting_id}/cleanup-audio")
@limiter.limit("10/minute")  # Cleanup operations
def cleanup_meeting_audio_endpoint(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Manually clean up audio files for a meeting.
    This endpoint allows users to free up storage space by deleting audio files
    after the meeting has been summarized.
    """
    # Verify the meeting exists and belongs to the current user
    meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check if meeting has been summarized (has summary or is ended)
    has_summary = crud.get_latest_meeting_summary(db, meeting_id) is not None
    is_ended = meeting.is_ended
    
    if not has_summary and not is_ended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cleanup audio files for a meeting that hasn't been summarized or ended"
        )
    
    try:
        cleanup_stats = cleanup_meeting_audio_files(meeting_id, current_user.email)
        
        # Log the cleanup action
        log_audit_event("audio_cleanup", current_user.id, "meeting", meeting_id, {
            "cleanup_stats": cleanup_stats
        })
        
        return {
            "message": "Audio files cleaned up successfully",
            "meeting_id": meeting_id,
            "cleanup_stats": cleanup_stats
        }
        
    except Exception as e:
        print(f"Error during manual audio cleanup for meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup audio files: {str(e)}"
        )

@app.get("/user/storage-usage")
@limiter.limit("30/minute")  # Storage info
def get_user_storage_usage(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get storage usage information for the current user.
    Shows total storage used by audio files across all meetings.
    """
    try:
        safe_email = get_safe_email_for_path(current_user.email)
        user_meetings_dir = f"/tmp/meetings/{safe_email}"
        
        total_size = 0
        total_files = 0
        meetings_with_audio = 0
        meeting_details = []
        
        # Get all user meetings
        user_meetings = db.query(models.Meeting).filter(
            models.Meeting.owner_id == current_user.id
        ).all()
        
        for meeting in user_meetings:
            meeting_audio_files = get_meeting_audio_files(meeting.id, current_user.email)
            
            if meeting_audio_files:
                meetings_with_audio += 1
                meeting_size = 0
                
                for audio_file in meeting_audio_files:
                    try:
                        file_size = os.path.getsize(audio_file)
                        meeting_size += file_size
                        total_files += 1
                    except Exception as e:
                        print(f"Error getting size for {audio_file}: {e}")
                
                total_size += meeting_size
                
                # Check if meeting has been summarized
                has_summary = crud.get_latest_meeting_summary(db, meeting.id) is not None
                
                meeting_details.append({
                    "meeting_id": meeting.id,
                    "meeting_title": meeting.title,
                    "audio_files_count": len(meeting_audio_files),
                    "total_size_bytes": meeting_size,
                    "total_size_mb": round(meeting_size / (1024 * 1024), 2),
                    "has_summary": has_summary,
                    "is_ended": meeting.is_ended,
                    "can_cleanup": has_summary or meeting.is_ended
                })
        
        return {
            "user_email": current_user.email,
            "total_storage_bytes": total_size,
            "total_storage_mb": round(total_size / (1024 * 1024), 2),
            "total_storage_gb": round(total_size / (1024 * 1024 * 1024), 3),
            "total_files": total_files,
            "total_meetings": len(user_meetings),
            "meetings_with_audio": meetings_with_audio,
            "auto_cleanup_enabled": settings.AUTO_CLEANUP_AUDIO_FILES,
            "meeting_details": meeting_details
        }
        
    except Exception as e:
        print(f"Error getting storage usage for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage usage: {str(e)}"
        )

async def generate_tags_with_chatgpt(meeting_id: int, db: Session) -> List[str]:
    """
    Generate 2-5 relevant tags for a meeting using ChatGPT based on meeting transcriptions and summary.
    """
    try:
        # Check if OpenAI API key is available
        if not settings.OPENAI_API_KEY:
            return []
        
        # Get all transcriptions for the meeting
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).order_by(models.Transcription.timestamp).all()
        
        # Get the latest summary if available
        latest_summary = crud.get_latest_meeting_summary(db, meeting_id)
        
        if not transcriptions and not latest_summary:
            return []
        
        # Combine transcription text and summary for context
        context_text = ""
        
        if transcriptions:
            for transcription in transcriptions:
                speaker = transcription.speaker or "Unknown"
                text = transcription.text or ""
                context_text += f"{speaker}: {text}\n"
        
        if latest_summary:
            try:
                # Try to parse as JSON to get summary content
                parsed_content = json.loads(latest_summary.content)
                if isinstance(parsed_content, dict) and "summary" in parsed_content:
                    context_text += f"\nSummary: {parsed_content['summary']}"
                else:
                    context_text += f"\nSummary: {latest_summary.content}"
            except (json.JSONDecodeError, TypeError):
                context_text += f"\nSummary: {latest_summary.content}"
        
        if not context_text.strip():
            return []
        
        # Initialize OpenAI client with explicit parameters only
        try:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # Explicit timeout
                max_retries=2   # Explicit retry count
            )
        except TypeError:
            # Fallback for older OpenAI library versions
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prompt for tag generation
        prompt = """I will give you meeting content (transcriptions and summary). Please analyze it and generate 2-5 relevant tags that best categorize this meeting. Please respond in English only.

The tags should be:
- Short (1-3 words each)
- Descriptive of the main topics, themes, or purpose
- Useful for organizing and filtering meetings
- Professional and clear

Return only the tags as a comma-separated list, nothing else.

Examples of good tags: "project planning", "budget review", "team sync", "client meeting", "strategy", "quarterly review", "product launch", "technical discussion"

Here is the meeting content:"""
        
        # Call ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at categorizing and tagging meeting content. You generate concise, relevant tags that help organize meetings effectively. Always respond in English only."
                },
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n{context_text}"
                }
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        tags_text = response.choices[0].message.content.strip()
        
        # Parse the comma-separated tags
        if tags_text:
            tags = [tag.strip().lower() for tag in tags_text.split(',') if tag.strip()]
            # Limit to 5 tags maximum
            return tags[:5]
        
        return []
        
    except Exception as e:
        print(f"Error generating tags with ChatGPT: {e}")
        return []

def cleanup_meeting_audio_files(meeting_id: int, user_email: str) -> dict:
    """
    Clean up all audio files related to a meeting after successful summarization.
    Returns a dictionary with cleanup statistics.
    """
    try:
        print(f"[AudioCleanup] Starting cleanup for meeting {meeting_id}")
        
        # Get all audio files for this meeting
        audio_files = get_meeting_audio_files(meeting_id, user_email)
        
        if not audio_files:
            print(f"[AudioCleanup] No audio files found for meeting {meeting_id}")
            return {
                "files_deleted": 0,
                "files_failed": 0,
                "total_size_freed": 0,
                "directories_cleaned": 0
            }
        
        deleted_count = 0
        failed_count = 0
        total_size_freed = 0
        directories_to_check = set()
        
        # Delete each audio file
        for audio_file in audio_files:
            try:
                # Get file size before deletion
                file_size = os.path.getsize(audio_file)
                
                # Delete the file
                os.remove(audio_file)
                deleted_count += 1
                total_size_freed += file_size
                
                # Track directory for cleanup
                directories_to_check.add(os.path.dirname(audio_file))
                
                print(f"[AudioCleanup] Deleted: {audio_file} ({file_size} bytes)")
                
            except Exception as e:
                failed_count += 1
                print(f"[AudioCleanup] Failed to delete {audio_file}: {e}")
        
        # Clean up empty directories
        directories_cleaned = 0
        for directory in directories_to_check:
            try:
                # Check if directory is empty
                if os.path.exists(directory) and not os.listdir(directory):
                    os.rmdir(directory)
                    directories_cleaned += 1
                    print(f"[AudioCleanup] Removed empty directory: {directory}")
                    
                    # Also try to remove parent directory if it's empty
                    parent_dir = os.path.dirname(directory)
                    if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                        directories_cleaned += 1
                        print(f"[AudioCleanup] Removed empty parent directory: {parent_dir}")
                        
            except Exception as e:
                print(f"[AudioCleanup] Failed to remove directory {directory}: {e}")
        
        cleanup_stats = {
            "files_deleted": deleted_count,
            "files_failed": failed_count,
            "total_size_freed": total_size_freed,
            "directories_cleaned": directories_cleaned
        }
        
        print(f"[AudioCleanup] Cleanup completed for meeting {meeting_id}: {cleanup_stats}")
        return cleanup_stats
        
    except Exception as e:
        print(f"[AudioCleanup] Error during cleanup for meeting {meeting_id}: {e}")
        return {
            "files_deleted": 0,
            "files_failed": 0,
            "total_size_freed": 0,
            "directories_cleaned": 0,
            "error": str(e)
        }

@app.get("/meetings/{meeting_id}/debug-audio")
@limiter.limit("30/minute")  # Debug endpoint
def debug_meeting_audio(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Debug endpoint to check audio file status for a meeting
    """
    try:
        # Verify meeting exists
        meeting = db.query(models.Meeting).filter(
            models.Meeting.id == meeting_id,
            models.Meeting.owner_id == current_user.id
        ).first()
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        safe_email = get_safe_email_for_path(current_user.email)
        user_meeting_dir = f"/tmp/meetings/{safe_email}/{meeting_id}"
        
        # Check directory structure
        debug_info = {
            "meeting_id": meeting_id,
            "user_email": current_user.email,
            "safe_email": safe_email,
            "expected_directory": user_meeting_dir,
            "directory_exists": os.path.exists(user_meeting_dir),
            "parent_directory_exists": os.path.exists(os.path.dirname(user_meeting_dir)),
            "files_in_directory": [],
            "audio_files_found": [],
            "transcriptions_count": 0,
            "meeting_status": meeting.status if hasattr(meeting, 'status') else "unknown"
        }
        
        # Check files in directory
        if os.path.exists(user_meeting_dir):
            try:
                all_files = os.listdir(user_meeting_dir)
                debug_info["files_in_directory"] = all_files
                
                # Filter audio files
                audio_extensions = ['.wav', '.webm', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
                audio_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in audio_extensions)]
                debug_info["audio_files_found"] = audio_files
                
                # Get file details
                file_details = []
                for file in audio_files:
                    file_path = os.path.join(user_meeting_dir, file)
                    try:
                        stat = os.stat(file_path)
                        file_details.append({
                            "name": file,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "is_readable": os.access(file_path, os.R_OK)
                        })
                    except Exception as e:
                        file_details.append({
                            "name": file,
                            "error": str(e)
                        })
                
                debug_info["file_details"] = file_details
                
            except Exception as e:
                debug_info["directory_error"] = str(e)
        
        # Check transcriptions
        transcriptions = db.query(models.Transcription).filter(
            models.Transcription.meeting_id == meeting_id
        ).all()
        
        debug_info["transcriptions_count"] = len(transcriptions)
        if transcriptions:
            debug_info["transcription_speakers"] = list(set([t.speaker for t in transcriptions if t.speaker]))
            debug_info["transcription_sample"] = [
                {"speaker": t.speaker, "text": t.text[:100] + "..." if len(t.text) > 100 else t.text}
                for t in transcriptions[:3]
            ]
        
        # Try to get audio files using the existing function
        try:
            audio_files_from_function = get_meeting_audio_files(meeting_id, current_user.email)
            debug_info["get_meeting_audio_files_result"] = {
                "count": len(audio_files_from_function),
                "files": [os.path.basename(f) for f in audio_files_from_function]
            }
        except Exception as e:
            debug_info["get_meeting_audio_files_error"] = str(e)
        
        return debug_info
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Debug] Error in debug_meeting_audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )

# Admin endpoints
@app.get("/admin/users", response_model=List[schemas.AdminUserList])
@limiter.limit("30/minute")
def get_all_users_admin(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users

@app.put("/admin/users/{user_id}/type")
@limiter.limit("20/minute")
def update_user_type_admin(
    request: Request,
    user_id: int,
    user_update: schemas.UserUpdateType,
    admin_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    updated_user = crud.update_user_type(db, user_id, user_update.user_type)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User type updated successfully", "user": updated_user}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    from config import settings
    import os
    from database import SessionLocal
    from models import User
    
    db = SessionLocal()
    users = db.query(User).all()
    user_list = [{"email": u.email, "user_type": str(u.user_type), "active": u.is_active} for u in users]
    db.close()
    
    return {
        "database_url": settings.DATABASE_URL,
        "environment": settings.ENVIRONMENT,
        "secret_key_length": len(settings.SECRET_KEY),
        "users_count": len(user_list),
        "users": user_list,
        "cwd": os.getcwd(),
        "env_vars": {
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT")
        }
    }

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # HTTPS/SSL Configuration for production
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    # Configure uvicorn with security settings
    uvicorn_config = {
        "app": "main:app",  # Use main FastAPI app
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "reload": os.getenv("ENVIRONMENT", "development") == "development",
        "access_log": True,
        "log_level": "info"
    }
    
    # Add SSL configuration if certificates are provided
    if ssl_keyfile and ssl_certfile and os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        uvicorn_config.update({
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile,
            "ssl_version": 3,  # TLS 1.2+
            "ssl_cert_reqs": 2,  # CERT_REQUIRED
            "ssl_ciphers": "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
        })
        app_logger.info("Starting server with HTTPS/SSL enabled")
    else:
        app_logger.warning("Starting server without HTTPS/SSL - not recommended for production")
    
    # Security headers for HTTPS
    if ssl_keyfile and ssl_certfile:
        # Update HSTS header for HTTPS
        @app.middleware("http")
        async def enforce_https_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            return response
    
    uvicorn.run(**uvicorn_config) 

# Export the main app for Railway deployment
app_instance = app
