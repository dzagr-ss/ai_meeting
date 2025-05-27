from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import openai
from openai import OpenAI
import models
import schemas
import config
import tempfile
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

# Password reset operations
def create_password_reset_token(db: Session, email: str) -> str:
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Set expiration time (1 hour from now)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Invalidate any existing tokens for this email
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.email == email,
        models.PasswordResetToken.used == False
    ).update({"used": True})
    
    # Create new token
    reset_token = models.PasswordResetToken(
        email=email,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    
    return token

def validate_password_reset_token(db: Session, token: str) -> Optional[models.PasswordResetToken]:
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    return reset_token

def reset_password(db: Session, token: str, new_password: str) -> bool:
    reset_token = validate_password_reset_token(db, token)
    if not reset_token:
        return False
    
    # Get the user
    user = get_user_by_email(db, reset_token.email)
    if not user:
        return False
    
    # Update password
    hashed_password = pwd_context.hash(new_password)
    user.hashed_password = hashed_password
    
    # Mark token as used
    reset_token.used = True
    
    db.commit()
    return True

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.settings.SECRET_KEY, algorithm=config.settings.ALGORITHM)
    return encoded_jwt

# Meeting operations
def create_meeting(db: Session, meeting: schemas.MeetingCreate, user_id: int):
    db_meeting = models.Meeting(**meeting.dict(), owner_id=user_id)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def get_meetings(db: Session, skip: int = 0, limit: int = 100, user_id: int = None):
    query = db.query(models.Meeting)
    if user_id:
        query = query.filter(models.Meeting.owner_id == user_id)
    return query.offset(skip).limit(limit).all()

def get_meeting(db: Session, meeting_id: int):
    return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()

def update_meeting(db: Session, meeting_id: int, meeting_update: schemas.MeetingUpdate, user_id: int):
    db_meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == user_id
    ).first()
    
    if not db_meeting:
        return None
    
    # Update only the fields that are provided
    update_data = meeting_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_meeting, field, value)
    
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def delete_meeting(db: Session, meeting_id: int, user_id: int):
    db_meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == user_id
    ).first()
    
    if not db_meeting:
        return False
    
    # Delete related records first (transcriptions, action items, summaries)
    db.query(models.Transcription).filter(models.Transcription.meeting_id == meeting_id).delete()
    db.query(models.ActionItem).filter(models.ActionItem.meeting_id == meeting_id).delete()
    db.query(models.Summary).filter(models.Summary.meeting_id == meeting_id).delete()
    
    # Delete the meeting
    db.delete(db_meeting)
    db.commit()
    return True

# Summary operations
def create_summary(db: Session, summary: schemas.SummaryCreate):
    db_summary = models.Summary(**summary.dict())
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def get_meeting_summaries(db: Session, meeting_id: int):
    return db.query(models.Summary).filter(
        models.Summary.meeting_id == meeting_id
    ).order_by(models.Summary.generated_at.desc()).all()

def get_latest_meeting_summary(db: Session, meeting_id: int):
    return db.query(models.Summary).filter(
        models.Summary.meeting_id == meeting_id
    ).order_by(models.Summary.generated_at.desc()).first()

# Transcription operations
async def process_audio(db: Session, meeting_id: int, audio_data: schemas.AudioData):
    # Initialize OpenAI client
    client = OpenAI(api_key=config.settings.OPENAI_API_KEY)
    
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data.audio_content)
            temp_file.flush()
            
            # Process audio with Whisper API
            with open(temp_file.name, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
        
        # Create transcription record
        transcription = models.Transcription(
            meeting_id=meeting_id,
            speaker="Unknown",  # You might want to implement speaker diarization here
            text=response.text
        )
        db.add(transcription)
        db.commit()
        db.refresh(transcription)
        
        # Generate action items using GPT
        action_items = await generate_action_items(response.text)
        for item in action_items:
            action_item = models.ActionItem(
                meeting_id=meeting_id,
                description=item,
                status="pending"
            )
            db.add(action_item)
        
        db.commit()
        return transcription
        
    except Exception as e:
        db.rollback()
        raise e

async def generate_action_items(text: str) -> list:
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract action items from the following meeting transcript. Return them as a list."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.split("\n")
    except Exception as e:
        return [] 