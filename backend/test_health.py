#!/usr/bin/env python3
"""
Simple test script to verify the health endpoint works correctly
"""
import requests
import subprocess
import time
import os
import sys

def test_health_endpoint():
    # Start the server in the background
    print('Starting server...')
    env = os.environ.copy()
    env['PORT'] = '8001'
    process = subprocess.Popen([
        'python', '-m', 'uvicorn', 'main:app', 
        '--host', '0.0.0.0', '--port', '8001'
    ], env=env)

    # Wait for server to start
    time.sleep(3)

    try:
        # Test health endpoint
        response = requests.get('http://localhost:8001/health')
        print(f'Health endpoint status: {response.status_code}')
        print(f'Health endpoint response: {response.text}')
        
        if response.status_code == 200:
            print('✅ Health endpoint working correctly!')
            return True
        else:
            print('❌ Health endpoint failed!')
            return False
            
    except Exception as e:
        print(f'❌ Error testing health endpoint: {e}')
        return False
    finally:
        # Stop the server
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1) 