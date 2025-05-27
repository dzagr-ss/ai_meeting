from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meetings = relationship("Meeting", back_populates="owner")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="scheduled")  # scheduled, in_progress, completed
    
    owner = relationship("User", back_populates="meetings")
    transcriptions = relationship("Transcription", back_populates="meeting")
    action_items = relationship("ActionItem", back_populates="meeting")
    summaries = relationship("Summary", back_populates="meeting")

class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    speaker = Column(String)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="transcriptions")

class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="summaries")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    description = Column(Text)
    assignee = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed
    
    meeting = relationship("Meeting", back_populates="action_items") 