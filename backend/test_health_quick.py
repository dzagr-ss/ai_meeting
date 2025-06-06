#!/usr/bin/env python3
"""
Quick test of health endpoints using FastAPI TestClient
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi.testclient import TestClient
    from main import app
    
    print("✅ Successfully imported main app and TestClient")
    
    # Create test client
    client = TestClient(app)
    
    # Test /health endpoint
    print("Testing /health endpoint...")
    response = client.get("/health")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ /health endpoint working!")
    else:
        print("❌ /health endpoint failed!")
    
    # Test /healthz endpoint  
    print("\nTesting /healthz endpoint...")
    response = client.get("/healthz")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ /healthz endpoint working!")
    else:
        print("❌ /healthz endpoint failed!")
    
    # Test /ready endpoint
    print("\nTesting /ready endpoint...")
    response = client.get("/ready")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ /ready endpoint working!")
    else:
        print("❌ /ready endpoint failed!")
    
    print("\n✅ All health endpoints are working correctly!")
    
except Exception as e:
    print(f"❌ Error testing health endpoints: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 