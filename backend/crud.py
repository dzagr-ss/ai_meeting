from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from passlib.context import CryptContext
import openai
from openai import OpenAI
import models
import schemas
import config
import tempfile
import secrets
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    # Set admin type for zagravsky@gmail.com, otherwise default to pending
    user_type = models.UserType.ADMIN if user.email == "zagravsky@gmail.com" else models.UserType.PENDING
    db_user = models.User(email=user.email, hashed_password=hashed_password, user_type=user_type)
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

# Tag operations
def create_tag(db: Session, tag: schemas.TagCreate):
    # Check if tag already exists (case-insensitive)
    existing_tag = db.query(models.Tag).filter(
        models.Tag.name == tag.name.lower()
    ).first()
    
    if existing_tag:
        return existing_tag
    
    db_tag = models.Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tag(db: Session, tag_id: int):
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tag_by_name(db: Session, name: str):
    return db.query(models.Tag).filter(models.Tag.name == name.lower()).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tag).offset(skip).limit(limit).all()

def update_tag(db: Session, tag_id: int, tag_update: schemas.TagUpdate):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    
    if not db_tag:
        return None
    
    update_data = tag_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int):
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    
    if not db_tag:
        return False
    
    db.delete(db_tag)
    db.commit()
    return True

def create_tags_from_names(db: Session, tag_names: List[str]) -> List[models.Tag]:
    """Create or get existing tags from a list of tag names"""
    tags = []
    for name in tag_names:
        if name.strip():
            tag = get_tag_by_name(db, name.strip())
            if not tag:
                tag_create = schemas.TagCreate(name=name.strip())
                tag = create_tag(db, tag_create)
            tags.append(tag)
    return tags

# Meeting operations
def create_meeting(db: Session, meeting: schemas.MeetingCreate, user_id: int):
    # Extract tag_ids from meeting data
    tag_ids = meeting.tag_ids if hasattr(meeting, 'tag_ids') else []
    meeting_data = meeting.dict()
    meeting_data.pop('tag_ids', None)  # Remove tag_ids from meeting data
    
    db_meeting = models.Meeting(**meeting_data, owner_id=user_id)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    
    # Add tags to the meeting
    if tag_ids:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
        db_meeting.tags.extend(tags)
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
    
    # Handle tag updates
    update_data = meeting_update.dict(exclude_unset=True)
    tag_ids = update_data.pop('tag_ids', None)
    
    # Update only the fields that are provided
    for field, value in update_data.items():
        setattr(db_meeting, field, value)
    
    # Update tags if provided
    if tag_ids is not None:
        # Clear existing tags
        db_meeting.tags.clear()
        # Add new tags
        if tag_ids:
            tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
            db_meeting.tags.extend(tags)
    
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def add_tags_to_meeting(db: Session, meeting_id: int, tag_names: List[str], user_id: int):
    """Add tags to a meeting by tag names, creating tags if they don't exist"""
    db_meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == user_id
    ).first()
    
    if not db_meeting:
        return None
    
    # Create or get existing tags
    tags = create_tags_from_names(db, tag_names)
    
    # Add tags to meeting (avoid duplicates)
    existing_tag_ids = {tag.id for tag in db_meeting.tags}
    for tag in tags:
        if tag.id not in existing_tag_ids:
            db_meeting.tags.append(tag)
    
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
    
    # Delete related records first (transcriptions, action items, summaries, meeting notes)
    db.query(models.Transcription).filter(models.Transcription.meeting_id == meeting_id).delete()
    db.query(models.ActionItem).filter(models.ActionItem.meeting_id == meeting_id).delete()
    db.query(models.Summary).filter(models.Summary.meeting_id == meeting_id).delete()
    db.query(models.MeetingNotes).filter(models.MeetingNotes.meeting_id == meeting_id).delete()
    
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
    # Initialize OpenAI client with defensive approach
    try:
        client = OpenAI(
            api_key=config.settings.OPENAI_API_KEY,
            timeout=60.0,  # Explicit timeout
            max_retries=2   # Explicit retry count
        )
    except TypeError:
        # Fallback for older OpenAI library versions
        client = OpenAI(api_key=config.settings.OPENAI_API_KEY)
    
    temp_file_path = None
    
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data.audio_content)
            temp_file.flush()
            temp_file_path = temp_file.name
            
            # Process audio with Whisper API
            with open(temp_file_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",
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
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary file {temp_file_path}: {cleanup_error}")

async def generate_action_items(text: str) -> list:
    try:
        # Initialize OpenAI client with defensive approach
        try:
            client = OpenAI(
                api_key=config.settings.OPENAI_API_KEY,
                timeout=60.0,  # Explicit timeout
                max_retries=2   # Explicit retry count
            )
        except TypeError:
            # Fallback for older OpenAI library versions
            client = OpenAI(api_key=config.settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract action items from the following meeting transcript. Return them as a list, one item per line. Always respond in English only."},
                {"role": "user", "content": text}
            ]
        )
        
        # Parse the response and split into individual action items
        action_items_text = response.choices[0].message.content
        action_items = [item.strip() for item in action_items_text.split("\n") if item.strip()]
        return action_items
    except Exception as e:
        print(f"Error generating action items: {e}")
        return []

# Meeting Notes operations
def create_meeting_notes(db: Session, meeting_notes: schemas.MeetingNotesCreate):
    db_meeting_notes = models.MeetingNotes(**meeting_notes.dict())
    db.add(db_meeting_notes)
    db.commit()
    db.refresh(db_meeting_notes)
    return db_meeting_notes

def get_meeting_notes(db: Session, meeting_id: int):
    return db.query(models.MeetingNotes).filter(
        models.MeetingNotes.meeting_id == meeting_id
    ).order_by(models.MeetingNotes.generated_at.desc()).all()

def get_latest_meeting_notes(db: Session, meeting_id: int):
    return db.query(models.MeetingNotes).filter(
        models.MeetingNotes.meeting_id == meeting_id
    ).order_by(models.MeetingNotes.generated_at.desc()).first()

# Meeting status operations
def mark_meeting_as_ended(db: Session, meeting_id: int, user_id: int):
    """Mark a meeting as ended and set the end time"""
    db_meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == user_id
    ).first()
    
    if not db_meeting:
        return None
    
    # Update meeting status
    db_meeting.is_ended = True
    db_meeting.end_time = datetime.utcnow()
    db_meeting.status = "completed"
    
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def get_meeting_status(db: Session, meeting_id: int, user_id: int):
    """Get the current status of a meeting"""
    db_meeting = db.query(models.Meeting).filter(
        models.Meeting.id == meeting_id,
        models.Meeting.owner_id == user_id
    ).first()
    
    if not db_meeting:
        return None
    
    return {
        "id": db_meeting.id,
        "is_ended": db_meeting.is_ended,
        "status": db_meeting.status,
        "end_time": db_meeting.end_time
    }

# Admin operations
def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def update_user_type(db: Session, user_id: int, new_user_type: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.user_type = models.UserType(new_user_type)
        db.commit()
        db.refresh(user)
    return user

def is_admin(user: models.User) -> bool:
    return user.user_type == models.UserType.ADMIN

def can_create_meetings(user: models.User) -> bool:
    return user.user_type in [models.UserType.ADMIN, models.UserType.TRIAL, models.UserType.NORMAL, models.UserType.PRO] 