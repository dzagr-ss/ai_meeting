from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Password reset schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

# Meeting schemas
class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class Meeting(MeetingBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    owner_id: int
    status: str

    class Config:
        from_attributes = True

# Transcription schemas
class TranscriptionBase(BaseModel):
    speaker: str
    text: str

class TranscriptionCreate(TranscriptionBase):
    meeting_id: int

class Transcription(TranscriptionBase):
    id: int
    meeting_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Action Item schemas
class ActionItemBase(BaseModel):
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None

class ActionItemCreate(ActionItemBase):
    meeting_id: int

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int
    status: str

    class Config:
        from_attributes = True

# Summary schemas
class SummaryBase(BaseModel):
    content: str

class SummaryCreate(SummaryBase):
    meeting_id: int

class Summary(SummaryBase):
    id: int
    meeting_id: int
    generated_at: datetime

    class Config:
        from_attributes = True

# Audio data schema
class AudioData(BaseModel):
    audio_content: bytes
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 

class SpeakerSegment(BaseModel):
    speaker: str
    start_time: float
    end_time: float
    text: str

class SpeakerIdentificationResponse(BaseModel):
    segments: List[SpeakerSegment]
    total_speakers: int 