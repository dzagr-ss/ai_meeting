import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

import models
import schemas


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, db_session):
        """Test creating a user"""
        user = models.User(
            email="test@example.com",
            hashed_password="hashed_password",
            user_type=models.UserType.NORMAL
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.user_type == models.UserType.NORMAL
        assert user.created_at is not None
    
    def test_user_email_unique_constraint(self, db_session):
        """Test that user email must be unique"""
        user1 = models.User(
            email="test@example.com",
            hashed_password="hashed_password1"
        )
        user2 = models.User(
            email="test@example.com",
            hashed_password="hashed_password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_type_enum(self, db_session):
        """Test UserType enum values"""
        user = models.User(
            email="admin@example.com",
            hashed_password="hashed_password",
            user_type=models.UserType.ADMIN
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_type == models.UserType.ADMIN
        assert user.user_type.value == "admin"


class TestTagModel:
    """Test Tag model"""
    
    def test_create_tag(self, db_session):
        """Test creating a tag"""
        tag = models.Tag(
            name="test-tag",
            color="#ff0000"
        )
        db_session.add(tag)
        db_session.commit()
        
        assert tag.id is not None
        assert tag.name == "test-tag"
        assert tag.color == "#ff0000"
        assert tag.created_at is not None
    
    def test_tag_name_unique_constraint(self, db_session):
        """Test that tag name must be unique"""
        tag1 = models.Tag(name="duplicate-tag")
        tag2 = models.Tag(name="duplicate-tag")
        
        db_session.add(tag1)
        db_session.commit()
        
        db_session.add(tag2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_tag_default_color(self, db_session):
        """Test tag default color"""
        tag = models.Tag(name="test-tag")
        db_session.add(tag)
        db_session.commit()
        
        assert tag.color == "#6366f1"


class TestMeetingModel:
    """Test Meeting model"""
    
    def test_create_meeting(self, db_session, test_user):
        """Test creating a meeting"""
        meeting = models.Meeting(
            title="Test Meeting",
            description="Test description",
            owner_id=test_user.id
        )
        db_session.add(meeting)
        db_session.commit()
        
        assert meeting.id is not None
        assert meeting.title == "Test Meeting"
        assert meeting.description == "Test description"
        assert meeting.owner_id == test_user.id
        assert meeting.status == "scheduled"
        assert meeting.is_ended is False
        assert meeting.start_time is not None
    
    def test_meeting_user_relationship(self, db_session, test_user):
        """Test meeting-user relationship"""
        meeting = models.Meeting(
            title="Test Meeting",
            owner_id=test_user.id
        )
        db_session.add(meeting)
        db_session.commit()
        
        assert meeting.owner == test_user
        assert meeting in test_user.meetings
    
    def test_meeting_tags_relationship(self, db_session, test_user, test_tag):
        """Test meeting-tags many-to-many relationship"""
        meeting = models.Meeting(
            title="Test Meeting",
            owner_id=test_user.id
        )
        meeting.tags.append(test_tag)
        db_session.add(meeting)
        db_session.commit()
        
        assert test_tag in meeting.tags
        assert meeting in test_tag.meetings


class TestTranscriptionModel:
    """Test Transcription model"""
    
    def test_create_transcription(self, db_session, test_meeting):
        """Test creating a transcription"""
        transcription = models.Transcription(
            meeting_id=test_meeting.id,
            speaker="Speaker 1",
            text="This is a test transcription"
        )
        db_session.add(transcription)
        db_session.commit()
        
        assert transcription.id is not None
        assert transcription.meeting_id == test_meeting.id
        assert transcription.speaker == "Speaker 1"
        assert transcription.text == "This is a test transcription"
        assert transcription.timestamp is not None
    
    def test_transcription_meeting_relationship(self, db_session, test_meeting):
        """Test transcription-meeting relationship"""
        transcription = models.Transcription(
            meeting_id=test_meeting.id,
            speaker="Speaker 1",
            text="Test text"
        )
        db_session.add(transcription)
        db_session.commit()
        
        assert transcription.meeting == test_meeting
        assert transcription in test_meeting.transcriptions


class TestSummaryModel:
    """Test Summary model"""
    
    def test_create_summary(self, db_session, test_meeting):
        """Test creating a summary"""
        summary = models.Summary(
            meeting_id=test_meeting.id,
            content="This is a test summary"
        )
        db_session.add(summary)
        db_session.commit()
        
        assert summary.id is not None
        assert summary.meeting_id == test_meeting.id
        assert summary.content == "This is a test summary"
        assert summary.generated_at is not None
    
    def test_summary_meeting_relationship(self, db_session, test_meeting):
        """Test summary-meeting relationship"""
        summary = models.Summary(
            meeting_id=test_meeting.id,
            content="Test summary"
        )
        db_session.add(summary)
        db_session.commit()
        
        assert summary.meeting == test_meeting
        assert summary in test_meeting.summaries


class TestPasswordResetTokenModel:
    """Test PasswordResetToken model"""
    
    def test_create_password_reset_token(self, db_session):
        """Test creating a password reset token"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = models.PasswordResetToken(
            email="test@example.com",
            token="test-token",
            expires_at=expires_at
        )
        db_session.add(token)
        db_session.commit()
        
        assert token.id is not None
        assert token.email == "test@example.com"
        assert token.token == "test-token"
        assert token.expires_at == expires_at
        assert token.used is False
        assert token.created_at is not None
    
    def test_token_unique_constraint(self, db_session):
        """Test that token must be unique"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token1 = models.PasswordResetToken(
            email="test1@example.com",
            token="duplicate-token",
            expires_at=expires_at
        )
        token2 = models.PasswordResetToken(
            email="test2@example.com",
            token="duplicate-token",
            expires_at=expires_at
        )
        
        db_session.add(token1)
        db_session.commit()
        
        db_session.add(token2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestActionItemModel:
    """Test ActionItem model"""
    
    def test_create_action_item(self, db_session, test_meeting):
        """Test creating an action item"""
        due_date = datetime.utcnow() + timedelta(days=7)
        action_item = models.ActionItem(
            meeting_id=test_meeting.id,
            description="Complete testing",
            assignee="John Doe",
            due_date=due_date
        )
        db_session.add(action_item)
        db_session.commit()
        
        assert action_item.id is not None
        assert action_item.meeting_id == test_meeting.id
        assert action_item.description == "Complete testing"
        assert action_item.assignee == "John Doe"
        assert action_item.due_date == due_date
        assert action_item.status == "pending"
    
    def test_action_item_meeting_relationship(self, db_session, test_meeting):
        """Test action item-meeting relationship"""
        action_item = models.ActionItem(
            meeting_id=test_meeting.id,
            description="Test task"
        )
        db_session.add(action_item)
        db_session.commit()
        
        assert action_item.meeting == test_meeting
        assert action_item in test_meeting.action_items


class TestMeetingNotesModel:
    """Test MeetingNotes model"""
    
    def test_create_meeting_notes(self, db_session, test_meeting):
        """Test creating meeting notes"""
        notes = models.MeetingNotes(
            meeting_id=test_meeting.id,
            content="These are test meeting notes"
        )
        db_session.add(notes)
        db_session.commit()
        
        assert notes.id is not None
        assert notes.meeting_id == test_meeting.id
        assert notes.content == "These are test meeting notes"
        assert notes.generated_at is not None
    
    def test_meeting_notes_meeting_relationship(self, db_session, test_meeting):
        """Test meeting notes-meeting relationship"""
        notes = models.MeetingNotes(
            meeting_id=test_meeting.id,
            content="Test notes"
        )
        db_session.add(notes)
        db_session.commit()
        
        assert notes.meeting == test_meeting
        assert notes in test_meeting.meeting_notes 