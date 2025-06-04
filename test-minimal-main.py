#!/usr/bin/env python3
"""
Minimal test version of main.py for Railway debugging
Only includes essential imports and health endpoints
"""

import sys
import os
import logging

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
from fastapi import FastAPI

app = FastAPI(
    title="Minimal Test API",
    description="Minimal test API for Railway debugging",
    version="1.0.0"
)

print("✅ FastAPI app created")

# Add ultra-simple health check endpoints
@app.get("/health")
async def health_check():
    """Ultra-simple health check endpoint"""
    return {"status": "ok", "message": "minimal test api working"}

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
        "message": "Minimal Test API",
        "status": "healthy",
        "python_version": sys.version,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

print("✅ All endpoints registered")

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