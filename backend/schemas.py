from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import re
import html

# Security constants
MAX_TEXT_LENGTH = 10000
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 1000
MAX_SPEAKER_NAME_LENGTH = 100

def sanitize_text(text: str) -> str:
    """Sanitize text input to prevent XSS and other attacks"""
    if not text:
        return text
    # HTML escape
    text = html.escape(text)
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

def validate_no_sql_injection(text: str) -> str:
    """Basic SQL injection prevention - improved to avoid false positives"""
    if not text:
        return text
        
    # More specific dangerous patterns that target actual SQL injection attempts
    dangerous_patterns = [
        r'(\bSELECT\b\s+[\w\*\,\s]+\s+\bFROM\b\s+[a-zA-Z_][a-zA-Z0-9_]*(\s|$|;))',  # SELECT columns FROM table_name
        r'(\bINSERT\b\s+\bINTO\b\s+[a-zA-Z_][a-zA-Z0-9_]*)',  # INSERT INTO table_name
        r'(\bUPDATE\b\s+[a-zA-Z_][a-zA-Z0-9_]*\s+\bSET\b)',   # UPDATE table_name SET
        r'(\bDELETE\b\s+\bFROM\b\s+[a-zA-Z_][a-zA-Z0-9_]*)', # DELETE FROM table_name
        r'(\bDROP\b\s+(TABLE|DATABASE|INDEX)\s+[a-zA-Z_][a-zA-Z0-9_]*)',  # DROP TABLE/DATABASE/INDEX name
        r'(\bCREATE\b\s+(TABLE|DATABASE|INDEX)\s+[a-zA-Z_][a-zA-Z0-9_]*)',  # CREATE TABLE/DATABASE/INDEX name
        r'(\bALTER\b\s+TABLE\s+[a-zA-Z_][a-zA-Z0-9_]*)',     # ALTER TABLE name
        r'(\bEXEC\b\s*\()',               # EXEC(
        r'(\bUNION\b\s+\bSELECT\b)',      # UNION SELECT
        r'(--|#|/\*|\*/)',                # SQL comments
        r'(\'\s*\bOR\b\s*\')',            # ' OR ' (quoted OR)
        r'(\"\s*\bOR\b\s*\")',            # " OR " (quoted OR)
        r'(\b1\s*=\s*1\b)',               # 1=1
        r'(\b0\s*=\s*0\b)',               # 0=0
        r'(\'\s*\bOR\b\s*\'\s*=\s*\')',   # ' OR '=' (classic injection)
        r'(\bOR\b\s+\d+\s*=\s*\d+)',     # OR 1=1 style
        r'(\bAND\b\s+\d+\s*=\s*\d+)',    # AND 1=1 style
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError('Input contains potentially dangerous content')
    return text

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class User(UserBase):
    id: int
    is_active: bool
    user_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('token')
    def validate_token(cls, v):
        # Basic token format validation
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid token format')
        return v

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# Tag schemas
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field("#6366f1", pattern=r"^#[0-9A-Fa-f]{6}$")

    @validator('name')
    def validate_name(cls, v):
        v = sanitize_text(v)
        v = validate_no_sql_injection(v)
        if not v.strip():
            raise ValueError('Tag name cannot be empty')
        return v.strip().lower()  # Normalize tag names to lowercase

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = sanitize_text(v)
            v = validate_no_sql_injection(v)
            if not v.strip():
                raise ValueError('Tag name cannot be empty')
            return v.strip().lower()
        return v

class Tag(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Meeting schemas
class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)

    @validator('title')
    def validate_title(cls, v):
        v = sanitize_text(v)
        v = validate_no_sql_injection(v)
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = sanitize_text(v)
            # Skip SQL injection validation for descriptions as they contain natural text
            # v = validate_no_sql_injection(v)  # Commented out to avoid false positives
        return v

class MeetingCreate(MeetingBase):
    tag_ids: Optional[List[int]] = Field(default_factory=list)

class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    tag_ids: Optional[List[int]] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            v = sanitize_text(v)
            v = validate_no_sql_injection(v)
            if not v.strip():
                raise ValueError('Title cannot be empty')
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = sanitize_text(v)
            v = validate_no_sql_injection(v)
        return v

class Meeting(MeetingBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    owner_id: int
    status: str
    is_ended: bool = False
    tags: List[Tag] = Field(default_factory=list)

    class Config:
        from_attributes = True

# Transcription schemas
class TranscriptionBase(BaseModel):
    speaker: str = Field(..., min_length=1, max_length=MAX_SPEAKER_NAME_LENGTH)
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)

    @validator('speaker')
    def validate_speaker(cls, v):
        v = sanitize_text(v)
        v = validate_no_sql_injection(v)
        if not v.strip():
            raise ValueError('Speaker name cannot be empty')
        # Only allow alphanumeric, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', v):
            raise ValueError('Speaker name contains invalid characters')
        return v

    @validator('text')
    def validate_text(cls, v):
        v = sanitize_text(v)
        # Skip SQL injection validation for transcription text as it contains natural speech
        # v = validate_no_sql_injection(v)  # Commented out to avoid false positives
        if not v.strip():
            raise ValueError('Transcription text cannot be empty')
        return v

class TranscriptionCreate(TranscriptionBase):
    meeting_id: int = Field(..., gt=0)

class Transcription(TranscriptionBase):
    id: int
    meeting_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Action Item schemas
class ActionItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    assignee: Optional[str] = Field(None, max_length=MAX_SPEAKER_NAME_LENGTH)
    due_date: Optional[datetime] = None

    @validator('description')
    def validate_description(cls, v):
        v = sanitize_text(v)
        # Skip SQL injection validation for action item descriptions as they contain natural text
        # v = validate_no_sql_injection(v)  # Commented out to avoid false positives
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v

    @validator('assignee')
    def validate_assignee(cls, v):
        if v is not None:
            v = sanitize_text(v)
            v = validate_no_sql_injection(v)
            if not re.match(r'^[a-zA-Z0-9\s\-_.@]+$', v):
                raise ValueError('Assignee name contains invalid characters')
        return v

class ActionItemCreate(ActionItemBase):
    meeting_id: int = Field(..., gt=0)

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int
    status: str

    class Config:
        from_attributes = True

# Summary schemas
class SummaryBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)

    @validator('content')
    def validate_content(cls, v):
        v = sanitize_text(v)
        # Skip SQL injection validation for content as it contains natural text
        # v = validate_no_sql_injection(v)  # Commented out to avoid false positives
        if not v.strip():
            raise ValueError('Summary content cannot be empty')
        return v

class SummaryCreate(SummaryBase):
    meeting_id: int = Field(..., gt=0)

class Summary(SummaryBase):
    id: int
    meeting_id: int
    generated_at: datetime

    class Config:
        from_attributes = True

# Audio data schema
class AudioData(BaseModel):
    audio_content: bytes = Field(..., max_length=50*1024*1024)  # 50MB limit
    format: str = Field(default="wav", pattern=r'^(wav|mp3|m4a|flac)$')
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    channels: int = Field(default=1, ge=1, le=2)

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 

class SpeakerSegment(BaseModel):
    speaker: str = Field(..., min_length=1, max_length=MAX_SPEAKER_NAME_LENGTH)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)

    @validator('speaker')
    def validate_speaker(cls, v):
        v = sanitize_text(v)
        if not re.match(r'^[a-zA-Z0-9\s\-_.]+$', v):
            raise ValueError('Speaker name contains invalid characters')
        return v

    @validator('text')
    def validate_text(cls, v):
        v = sanitize_text(v)
        return v

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be greater than start time')
        return v

class SpeakerIdentificationResponse(BaseModel):
    segments: List[SpeakerSegment]
    total_speakers: int = Field(..., ge=0, le=50)  # Reasonable limit

# Meeting Notes schemas
class MeetingNotesBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)

    @validator('content')
    def validate_content(cls, v):
        v = sanitize_text(v)
        # Skip SQL injection validation for notes content as it contains natural text
        # v = validate_no_sql_injection(v)  # Commented out to avoid false positives
        if not v.strip():
            raise ValueError('Notes content cannot be empty')
        return v

class MeetingNotesCreate(MeetingNotesBase):
    meeting_id: int = Field(..., gt=0)

class MeetingNotes(MeetingNotesBase):
    id: int
    meeting_id: int
    generated_at: datetime

    class Config:
        from_attributes = True

# Admin schemas
class UserUpdateType(BaseModel):
    user_type: str = Field(..., pattern="^(admin|pending|trial|normal|pro)$")

class AdminUserList(BaseModel):
    id: int
    email: str
    user_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True 