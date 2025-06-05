#!/usr/bin/env python3
"""
Test WebSocket connection for live transcription
"""
import asyncio
import websockets
import json
import numpy as np

async def test_websocket():
    # Connect to the WebSocket endpoint
    uri = "ws://localhost:8000/ws/meetings/1/stream"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send authentication message
            auth_message = {
                "type": "auth",
                "token": "test-token"  # This will fail auth but test connection
            }
            await websocket.send(json.dumps(auth_message))
            print("📤 Sent authentication message")
            
            # Listen for responses
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response received (likely auth failed as expected)")
                
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket connection...")
    asyncio.run(test_websocket()) 