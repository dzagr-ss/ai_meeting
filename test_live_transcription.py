#!/usr/bin/env python3
"""
Test live transcription end-to-end pipeline
"""
import asyncio
import websockets
import json
import requests
import base64
import numpy as np

# Test configuration
BASE_URL = "http://localhost:8000"

async def test_live_transcription():
    print("🧪 Testing Live Transcription Pipeline...")
    
    # Step 1: Create a test user
    print("\n1️⃣  Creating test user...")
    user_data = {
        "email": "test@livetranscription.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/", json=user_data)
        if response.status_code == 400 and "already registered" in response.text:
            print("✅ User already exists")
        elif response.status_code in [200, 201]:
            print("✅ User created successfully")
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    # Step 2: Login to get token
    print("\n2️⃣  Logging in...")
    try:
        response = requests.post(f"{BASE_URL}/token", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error logging in: {e}")
        return
    
    # Step 3: Create a meeting
    print("\n3️⃣  Creating meeting...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        meeting_data = {
            "title": "Live Transcription Test Meeting",
            "description": "Testing live transcription functionality"
        }
        response = requests.post(f"{BASE_URL}/meetings/", json=meeting_data, headers=headers)
        if response.status_code == 200:
            meeting_id = response.json()["id"]
            print(f"✅ Meeting created with ID: {meeting_id}")
        else:
            print(f"❌ Failed to create meeting: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating meeting: {e}")
        return
    
    # Step 4: Test WebSocket connection
    print("\n4️⃣  Testing WebSocket connection...")
    ws_url = f"ws://localhost:8000/ws/meetings/{meeting_id}/stream"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")
            
            # Send authentication
            auth_message = {
                "type": "auth",
                "token": token
            }
            await websocket.send(json.dumps(auth_message))
            print("📤 Sent authentication")
            
            # Note: The server doesn't send an auth response on success
            # It only closes the connection if auth fails
            # We'll proceed to send audio and see if we get responses
            print("✅ Authentication assumed successful (no error response)")
            
            # Step 5: Send mock audio data
            print("\n5️⃣  Sending mock audio data...")
            
            # Generate some mock audio chunks (simulate 16kHz mono audio)
            sample_rate = 16000
            chunk_duration = 0.1  # 100ms chunks
            chunk_size = int(sample_rate * chunk_duration)
            
            transcription_received = False
            
            for i in range(50):  # Send 50 chunks (5 seconds of audio)
                # Generate mock audio data (sine wave + noise)
                t = np.arange(chunk_size) / sample_rate + i * chunk_duration
                frequency = 440  # A4 note
                audio_data = 0.1 * np.sin(2 * np.pi * frequency * t) + 0.05 * np.random.randn(chunk_size)
                
                # Convert to Float32Array bytes (what the backend expects)
                audio_float32 = audio_data.astype(np.float32)
                audio_bytes = audio_float32.tobytes()
                
                # Send raw audio bytes (not JSON)
                await websocket.send(audio_bytes)
                
                # Check for transcription responses
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        if isinstance(response, str):
                            message = json.loads(response)
                            if message.get("type") == "transcription":
                                print(f"📥 Received transcription: {message}")
                                transcription_received = True
                            else:
                                print(f"📥 Received message: {message}")
                        else:
                            print(f"📥 Received binary data: {len(response)} bytes")
                except asyncio.TimeoutError:
                    pass  # No message received, continue
                
                # Small delay between chunks
                await asyncio.sleep(0.1)
            
            # Wait a bit more for any final transcriptions
            print("\n6️⃣  Waiting for final transcriptions...")
            for _ in range(30):  # Wait up to 3 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    if isinstance(response, str):
                        message = json.loads(response)
                        if message.get("type") == "transcription":
                            print(f"📥 Final transcription: {message}")
                            transcription_received = True
                        else:
                            print(f"📥 Final message: {message}")
                    else:
                        print(f"📥 Final binary data: {len(response)} bytes")
                except asyncio.TimeoutError:
                    continue
            
            # Final status
            if transcription_received:
                print("\n🎉 SUCCESS: Live transcription pipeline is working!")
            else:
                print("\n⚠️  No transcriptions received. Check mock audio processing.")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    print("🔬 Live Transcription End-to-End Test")
    print("=" * 50)
    asyncio.run(test_live_transcription()) 