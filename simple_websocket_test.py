#!/usr/bin/env python3
"""
Simple WebSocket test with detailed logging
"""
import asyncio
import websockets
import json
import requests
import numpy as np

async def simple_test():
    print("🔧 Simple WebSocket Test")
    
    # Get a valid token first
    print("Getting token...")
    try:
        response = requests.post("http://localhost:8000/token", json={
            "email": "test@livetranscription.com",
            "password": "TestPass123!"
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Got token: {token[:20]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return
    
    # Test WebSocket with more audio chunks
    ws_url = "ws://localhost:8000/ws/meetings/26/stream"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")
            
            # Authenticate
            auth_message = {"type": "auth", "token": token}
            await websocket.send(json.dumps(auth_message))
            print("📤 Sent auth")
            
            # Send more audio chunks to trigger segment generation
            print("📤 Sending test audio chunks...")
            
            for i in range(20):  # Send 20 chunks instead of 5
                # Generate larger audio chunk (1600 samples = ~100ms at 16kHz)
                audio_data = np.random.randn(1600).astype(np.float32)
                await websocket.send(audio_data.tobytes())
                print(f"📤 Sent chunk {i+1}: {len(audio_data.tobytes())} bytes")
                
                # Wait a bit and check for responses
                await asyncio.sleep(0.1)
                
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.05)
                        if isinstance(response, str):
                            message = json.loads(response)
                            print(f"🎉 JSON Response: {message}")
                        else:
                            print(f"📥 Binary Response: {len(response)} bytes")
                except asyncio.TimeoutError:
                    pass  # No response yet, continue
            
            # Wait longer for any final transcriptions
            print("⏳ Waiting for final responses...")
            for _ in range(50):  # Wait up to 5 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    if isinstance(response, str):
                        message = json.loads(response)
                        print(f"🎉 Final JSON Response: {message}")
                    else:
                        print(f"📥 Final Binary Response: {len(response)} bytes")
                except asyncio.TimeoutError:
                    continue
            
            print("✅ Test completed")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test()) 