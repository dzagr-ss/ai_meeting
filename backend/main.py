from fastapi import FastAPI, HTTPException, Depends, Request, status, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from fastapi.security import OAuth2PasswordBearer
import jwt
import base64
from datetime import datetime
import numpy as np
import io
from pydub import AudioSegment
import wave
import warnings
from fastapi.responses import JSONResponse
import glob

from database import get_db, engine, SessionLocal
import models
import schemas
import crud
from config import settings
from speaker_identification import create_speaker_identifier
import tempfile
from audio_processor import AudioChunker
import asyncio
import json
import time
import uuid
import google.generativeai as genai
from email_service import email_service

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meeting Transcription API",
    description="API for real-time meeting transcription and analysis",
    version="1.0.0"
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, replace with specific hosts
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")  # In production, use a secure secret key
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Suppress Whisper FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", module="whisper.transcribe")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Set this in your .env or environment

@app.get("/")
async def root():
    return {"message": "Welcome to Meeting Transcription API"}

@app.post("/users/", response_model=schemas.User)
@limiter.limit("5/minute")
async def create_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token")
@limiter.limit("10/minute")
async def login(request: Request, user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = crud.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/password-reset/request")
@limiter.limit("3/minute")
async def request_password_reset(request: Request, reset_request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset token to be sent via email"""
    # Check if user exists
    user = crud.get_user_by_email(db, reset_request.email)
    if not user:
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
    except jwt.PyJWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

@app.post("/meetings/", response_model=schemas.Meeting)
def create_meeting(
    meeting: schemas.MeetingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Set default meeting title if not provided
    if not meeting.title:
        current_time = datetime.now()
        meeting.title = current_time.strftime("%Y-%m-%d %H:%M")
    
    return crud.create_meeting(db=db, meeting=meeting, user_id=current_user.id)

@app.get("/meetings/", response_model=List[schemas.Meeting])
def get_meetings(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meetings = crud.get_meetings(db, skip=skip, limit=limit, user_id=current_user.id)
    return meetings

@app.put("/meetings/{meeting_id}", response_model=schemas.Meeting)
def update_meeting(
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
def delete_meeting(
    meeting_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.delete_meeting(db=db, meeting_id=meeting_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found or you don't have permission to delete it")
    return {"message": "Meeting deleted successfully"}

@app.get("/meetings/{meeting_id}/transcriptions", response_model=List[schemas.Transcription])
def get_meeting_transcriptions(
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
    return {
        "headers": {
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    }

@app.post("/meetings/{meeting_id}/transcribe")
async def transcribe_meeting(
    meeting_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Read the audio file content
        audio_content = await audio.read()
        
        # Save audio to /tmp/meeting_{meeting_id}_{timestamp}.wav
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"/tmp/meeting_{meeting_id}_{timestamp}.wav"
        with open(audio_filename, "wb") as f:
            f.write(audio_content)
        print(f"Audio saved to: {audio_filename}")
        
        # Create AudioData object
        audio_data = schemas.AudioData(
            audio_content=audio_content,
            format="wav",
            sample_rate=16000,
            channels=1
        )
        
        # Process the audio
        result = await crud.process_audio(db=db, meeting_id=meeting_id, audio_data=audio_data)
        
        # Return just the text
        return {"text": result.text}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/meetings/{meeting_id}/identify-speakers", response_model=schemas.SpeakerIdentificationResponse)
async def identify_speakers(
    meeting_id: int,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            # Write the uploaded audio to the temporary file
            audio_content = await audio.read()
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name

        try:
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
            
        finally:
            # Clean up the temporary file
            os.unlink(temp_audio_path)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    total_processed_count = 0 # Variable to keep track of the total processed segments (from SpeakerIdentifier)
    received_chunk_count = 0 # Variable to keep track of the total raw audio chunks received

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
                
            # Optional: verify user exists in DB if necessary for this endpoint
            # user = crud.get_user_by_email(db, email=email)
            # if user is None:
            #     await websocket.close(code=1008, reason="Invalid token: user not found")
            #     return

        except jwt.PyJWTError:
            await websocket.close(code=1008, reason="Invalid or expired token")
            return

        if settings.SHOW_BACKEND_LOGS:
            print(f"WebSocket connected and authenticated for meeting {meeting_id}")

        # Initialize speaker identifier after authentication
        speaker_identifier = create_speaker_identifier()
        if settings.SHOW_BACKEND_LOGS:
            print("Speaker identifier initialized")

        meeting_audio_time = 0.0  # Track total audio time since meeting start

        # Process incoming raw audio data (Float32Array bytes)
        while True:
            data = await websocket.receive_bytes()

            if isinstance(data, bytes):
                try:
                    received_chunk_count += 1
                    buffer_size_before = len(chunker.buffer)
                    if settings.SHOW_BACKEND_LOGS:
                        print(f"[WebSocket] Received chunk {received_chunk_count}: {len(data)} bytes. Chunker buffer size before: {buffer_size_before}")
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

                         newly_processed_segments = speaker_identifier.process_audio_chunk(
                             processed_chunk,
                             abs_chunk_start_time
                         )
                         process_end = time.time()
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] SpeakerIdentifier returned {len(newly_processed_segments)} segments. Processing time: {process_end - process_start:.3f}s")

                         total_processed_count += len(newly_processed_segments)

                         finalized_segments = []
                         current_merged_segment = last_processed_segment

                         for segment in newly_processed_segments:
                              if current_merged_segment is None:
                                   current_merged_segment = segment
                              elif segment["speaker"] == current_merged_segment["speaker"] and segment["start_time"] - current_merged_segment["end_time"] <= time_tolerance:
                                   current_merged_segment["text"] += " " + segment["text"]
                                   current_merged_segment["end_time"] = segment["end_time"]
                              else:
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
                                           "end_time": final_segment["end_time"],
                                           "processed_count": len(newly_processed_segments),
                                           "total_processed_count": total_processed_count,
                                           "received_chunk_count": received_chunk_count,
                                           "speaker_buffer_duration": speaker_identifier.get_buffer_duration_seconds(),
                                           "chunker_processed_count": chunker.get_processed_chunk_yield_count()
                                       }
                                   })
                              if settings.SHOW_BACKEND_LOGS:
                                  print("[WebSocket] Finished sending finalized segments for this chunk.")

                         print(f"[WebSocket] Pending last_processed_segment for next chunk: {last_processed_segment}")
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Current total processed count: {total_processed_count}")
                         if settings.SHOW_BACKEND_LOGS:
                             print(f"[WebSocket] Processed segments in this interval: {len(newly_processed_segments)}, Speaker buffer duration: {speaker_identifier.get_buffer_duration_seconds():.2f}s, Chunker processed: {chunker.get_processed_chunk_yield_count()}")

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
        if speaker_identifier and hasattr(speaker_identifier, "audio_buffer"):
            if len(speaker_identifier.audio_buffer) > 0:
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
                speaker_identifier.audio_buffer = np.array([], dtype=np.float32)

    except Exception as e:
        print(f"WebSocket error for meeting {meeting_id}: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
    finally:
        if chunker:
            chunker.cleanup()
            if settings.SHOW_BACKEND_LOGS:
                print("Cleaned up chunker resources")

@app.post("/api/summarize-audio/")
async def summarize_audio(audio: UploadFile = File(...)):
    # TODO: Save file, run Gemini summary, etc.
    summary = "This is a dummy summary."  # Replace with real logic
    return JSONResponse({"summary": summary})

@app.get("/meetings/{meeting_id}/summaries", response_model=List[schemas.Summary])
def get_meeting_summaries(
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

@app.get("/api/meeting/{meeting_id}/summary")
async def get_meeting_summary(meeting_id: int, db: Session = Depends(get_db)):
    # First check if we have a stored summary
    stored_summary = crud.get_latest_meeting_summary(db, meeting_id)
    if stored_summary:
        return {"summary": stored_summary.content}
    
    # If no stored summary, generate a new one
    audio_files = get_meeting_audio_files(meeting_id)
    if not audio_files:
        return JSONResponse({"summary": None, "error": "No audio files found for this meeting"}, status_code=404)
    try:
        summary_content = summarize_with_gemini_multiple_files(audio_files)
        
        # Save the generated summary to database
        summary_create = schemas.SummaryCreate(
            meeting_id=meeting_id,
            content=summary_content
        )
        crud.create_summary(db, summary_create)
        
        return {"summary": summary_content}
    except Exception as e:
        return JSONResponse({"summary": None, "error": f"Gemini error: {str(e)}"}, status_code=500)

def get_meeting_audio_files(meeting_id: int) -> List[str]:
    # Find all audio files for the given meeting_id
    pattern = f"/tmp/meeting_{meeting_id}_*.wav"
    files = glob.glob(pattern)
    # Sort by timestamp (filename contains timestamp)
    files.sort()
    return files

def summarize_with_gemini_multiple_files(audio_files: List[str]) -> str:
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
        
        # Initialize Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
        
        # Prepare the prompt and content
        file_list = ", ".join([f.split('/')[-1] for f in audio_files])
        prompt = f"Summarize the main points and action items from this meeting audio. Files processed: {file_list}"
        parts = [
            {"text": prompt},
            {"inline_data": {"mime_type": "audio/wav", "data": base64_audio}},
        ]
        
        # Call Gemini
        response = model.generate_content(parts)
        return response.text or "No summary generated."
    
    return "No audio data found."

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
    prompt = "Summarize the main points and action items from this meeting audio."
    parts = [
        {"text": prompt},
        {"inline_data": {"mime_type": "audio/wav", "data": base64_audio}},
    ]

    # Call Gemini
    response = model.generate_content(parts)
    return response.text or "No summary generated."

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    uvicorn.run(app, host="0.0.0.0", port=8000) 