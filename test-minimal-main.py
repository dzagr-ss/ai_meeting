#!/usr/bin/env python3
"""
Minimal test version of main.py for Railway debugging
Only includes essential imports and health endpoints
"""

import sys
import os
import logging
import base64
import json

print("=== Minimal FastAPI Test Starting ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")

# Test basic imports
try:
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"✅ Uvicorn: {uvicorn.__version__}")
except Exception as e:
    print(f"❌ Uvicorn import failed: {e}")
    sys.exit(1)

# Test pydantic import
try:
    # Compatible imports for both Pydantic v1 and v2
    try:
        # Pydantic v2 import
        from pydantic_settings import BaseSettings
        print("✅ Pydantic v2 BaseSettings")
    except ImportError:
        # Pydantic v1 fallback
        from pydantic import BaseSettings
        print("✅ Pydantic v1 BaseSettings")
except Exception as e:
    print(f"❌ Pydantic BaseSettings import failed: {e}")
    sys.exit(1)

# Create minimal FastAPI app
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Minimal Test API",
    description="Minimal test API for Railway debugging with CORS support",
    version="1.0.0"
)

print("✅ FastAPI app created")

# Add CORS middleware to solve the original issue
allowed_origins = [
    "https://ai-meeting-indol.vercel.app",  # Vercel frontend
    "http://localhost:3000",  # Local development
    "http://127.0.0.1:3000",  # Local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Cache-Control"
    ],
    expose_headers=["X-Total-Count"],
    max_age=600,  # Cache preflight for 10 minutes
)

print(f"✅ CORS middleware added with origins: {allowed_origins}")

# Add ultra-simple health check endpoints
@app.get("/health")
async def health_check():
    """Ultra-simple health check endpoint"""
    return {"status": "ok", "message": "minimal test api working with CORS"}

@app.get("/healthz")  
async def health_check_alt():
    """Alternative health check endpoint"""
    return {"alive": True, "ready": True}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return "pong"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Minimal Test API with CORS",
        "status": "healthy",
        "python_version": sys.version,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "cors_enabled": True,
        "allowed_origins": allowed_origins
    }

# Add a test endpoint for CORS testing
@app.post("/test-cors")
async def test_cors():
    """Test endpoint for CORS functionality"""
    return {
        "message": "CORS test successful",
        "method": "POST",
        "timestamp": "2025-06-04T20:52:00Z"
    }

# Add basic token endpoint for authentication
@app.post("/token")
async def token_endpoint():
    """Basic token endpoint for testing authentication"""
    # Create a proper JWT structure that can be parsed by JWT libraries
    header = {
        "typ": "JWT",
        "alg": "HS256"
    }
    
    payload = {
        "sub": "test@example.com",
        "exp": 1733349200,  # Future expiration
        "iat": 1733262800,  # Issued at
        "user_id": 1,
        "email": "test@example.com"
    }
    
    # Base64 encode header and payload (like a real JWT)
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = "test_signature_for_development"
    
    # Construct proper JWT token
    jwt_token = f"{header_b64}.{payload_b64}.{signature}"
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer"
    }

# Add basic meetings endpoints
@app.get("/meetings/")
async def get_meetings(request: Request):
    """Basic meetings list endpoint - returns array directly"""
    # Check for authorization header (but accept any value for testing)
    auth_header = request.headers.get("authorization", "")
    print(f"[DEBUG] GET /meetings/ - Auth header: {auth_header[:50]}..." if auth_header else "[DEBUG] GET /meetings/ - No auth header")
    
    # Return an empty array directly (what frontend expects)
    meetings = []
    return meetings

@app.post("/meetings/")
async def create_meeting(request: Request):
    """Basic meeting creation endpoint with mock authentication"""
    # Check for authorization header (but accept any value for testing)
    auth_header = request.headers.get("authorization", "")
    print(f"[DEBUG] POST /meetings/ - Auth header: {auth_header[:50]}..." if auth_header else "[DEBUG] POST /meetings/ - No auth header")
    
    # Log request info without reading body (which might cause issues)
    print(f"[DEBUG] POST /meetings/ - Content-Type: {request.headers.get('content-type', 'none')}")
    print(f"[DEBUG] POST /meetings/ - Method: {request.method}")
    print(f"[DEBUG] POST /meetings/ - URL: {request.url}")
    
    # Mock meeting creation - return format that matches frontend expectations
    meeting = {
        "id": 1,
        "title": "Test Meeting",
        "description": None,  # Frontend expects description field
        "start_time": "2025-06-04T21:20:00Z",  # Frontend expects start_time, not created_at
        "end_time": None,  # Frontend expects end_time field
        "status": "scheduled",  # Use expected status values: scheduled, in_progress, completed
        "tags": []  # Frontend expects tags array
    }
    
    print(f"[DEBUG] POST /meetings/ - Returning meeting: {meeting}")
    
    # Return explicit JSONResponse with status 201 (Created) and custom header
    return JSONResponse(
        content=meeting,
        status_code=201,
        headers={
            "Content-Type": "application/json",
            "X-Meeting-Created": "true",
            "X-Debug": "meeting-creation-successful",
            "Location": f"/meetings/{meeting['id']}"
        }
    )

# Add basic tags endpoint
@app.get("/tags/")
async def get_tags():
    """Basic tags list endpoint - returns array directly"""
    # Return an empty array directly (what frontend expects)
    tags = []
    return tags

print("✅ All endpoints registered with CORS support")

if __name__ == "__main__":
    print("=== Starting Uvicorn Server ===")
    
    # Get port from environment
    port = int(os.getenv("PORT", 8000))
    print(f"Port: {port}")
    
    # Start the server
    uvicorn.run(
        "test-minimal-main:app", 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        access_log=True
    ) 