#!/usr/bin/env python3
"""
Simple test to verify health endpoints can be imported and work
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the main app
    from main import app
    print("✅ Successfully imported main app")
    
    # Check if health endpoints are defined
    routes = [route.path for route in app.routes]
    health_routes = [route for route in routes if 'health' in route or 'ready' in route]
    
    print(f"Health-related routes found: {health_routes}")
    
    if '/health' in routes:
        print("✅ /health endpoint is defined")
    else:
        print("❌ /health endpoint is missing")
        
    if '/healthz' in routes:
        print("✅ /healthz endpoint is defined")
    else:
        print("❌ /healthz endpoint is missing")
        
    if '/ready' in routes:
        print("✅ /ready endpoint is defined")
    else:
        print("❌ /ready endpoint is missing")
        
    print("✅ Health endpoint configuration looks good!")
    
except Exception as e:
    print(f"❌ Error importing or checking app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 