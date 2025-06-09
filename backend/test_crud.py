import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

import crud
import schemas
import models


class TestUserCRUD:
    """Test user CRUD operations"""
    
    def test_create_user(self, db_session):
        """Test creating a user"""
        user_data = schemas.UserCreate(
            email="test@example.com",
            password="TestPassword123!"
        )
        user = crud.create_user(db_session, user_data)
        
        assert user.email == "test@example.com"
        assert user.hashed_password != "TestPassword123!"  # Should be hashed
        assert user.user_type == models.UserType.PENDING
        assert user.is_active is True
    
    def test_create_admin_user(self, db_session):
        """Test creating admin user with special email"""
        user_data = schemas.UserCreate(
            email="zagravsky@gmail.com",
            password="AdminPassword123!"
        )
        user = crud.create_user(db_session, user_data)
        
        assert user.email == "zagravsky@gmail.com"
        assert user.user_type == models.UserType.ADMIN
    
    def test_get_user(self, db_session, test_user):
        """Test getting a user by ID"""
        user = crud.get_user(db_session, test_user.id)
        assert user == test_user
        
        # Test non-existent user
        user = crud.get_user(db_session, 99999)
        assert user is None
    
    def test_get_user_by_email(self, db_session, test_user):
        """Test getting a user by email"""
        user = crud.get_user_by_email(db_session, test_user.email)
        assert user == test_user
        
        # Test non-existent email
        user = crud.get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None
    
    def test_authenticate_user(self, db_session, test_user_data):
        """Test user authentication"""
        # Create user first
        user_create = schemas.UserCreate(**test_user_data)
        user = crud.create_user(db_session, user_create)
        
        # Test correct password
        authenticated_user = crud.authenticate_user(
            db_session, 
            test_user_data["email"], 
            test_user_data["password"]
        )
        assert authenticated_user == user
        
        # Test wrong password
        authenticated_user = crud.authenticate_user(
            db_session, 
            test_user_data["email"], 
            "wrong_password"
        )
        assert authenticated_user is False
        
        # Test non-existent user
        authenticated_user = crud.authenticate_user(
            db_session, 
            "nonexistent@example.com", 
            "password"
        )
        assert authenticated_user is False
    
    def test_create_access_token(self):
        """Test creating access token"""
        data = {"sub": "test@example.com"}
        token = crud.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0


class TestPasswordResetCRUD:
    """Test password reset CRUD operations"""
    
    def test_create_password_reset_token(self, db_session):
        """Test creating password reset token"""
        email = "test@example.com"
        token = crud.create_password_reset_token(db_session, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token exists in database
        reset_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.email == email,
            models.PasswordResetToken.token == token
        ).first()
        
        assert reset_token is not None
        assert reset_token.used is False
        assert reset_token.expires_at > datetime.utcnow()
    
    def test_create_password_reset_token_invalidates_old(self, db_session):
        """Test that creating new token invalidates old ones"""
        email = "test@example.com"
        
        # Create first token
        token1 = crud.create_password_reset_token(db_session, email)
        
        # Create second token
        token2 = crud.create_password_reset_token(db_session, email)
        
        # First token should be marked as used
        old_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token1
        ).first()
        
        assert old_token.used is True
        
        # New token should be valid
        new_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token2
        ).first()
        
        assert new_token.used is False
    
    def test_validate_password_reset_token(self, db_session):
        """Test validating password reset token"""
        email = "test@example.com"
        token = crud.create_password_reset_token(db_session, email)
        
        # Test valid token
        reset_token = crud.validate_password_reset_token(db_session, token)
        assert reset_token is not None
        assert reset_token.email == email
        
        # Test invalid token
        reset_token = crud.validate_password_reset_token(db_session, "invalid_token")
        assert reset_token is None
    
    def test_reset_password(self, db_session, test_user_data):
        """Test resetting password"""
        # Create user
        user_create = schemas.UserCreate(**test_user_data)
        user = crud.create_user(db_session, user_create)
        
        # Create reset token
        token = crud.create_password_reset_token(db_session, user.email)
        
        # Reset password
        new_password = "NewPassword123!"
        success = crud.reset_password(db_session, token, new_password)
        
        assert success is True
        
        # Verify user can authenticate with new password
        authenticated_user = crud.authenticate_user(
            db_session, 
            user.email, 
            new_password
        )
        assert authenticated_user == user
        
        # Verify token is marked as used
        reset_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token
        ).first()
        assert reset_token.used is True


class TestTagCRUD:
    """Test tag CRUD operations"""
    
    def test_create_tag(self, db_session):
        """Test creating a tag"""
        tag_data = schemas.TagCreate(name="test-tag", color="#ff0000")
        tag = crud.create_tag(db_session, tag_data)
        
        assert tag.name == "test-tag"
        assert tag.color == "#ff0000"
    
    def test_create_duplicate_tag(self, db_session):
        """Test creating duplicate tag returns existing"""
        tag_data = schemas.TagCreate(name="duplicate")
        
        # Create first tag
        tag1 = crud.create_tag(db_session, tag_data)
        
        # Create "duplicate" tag should return existing
        tag2 = crud.create_tag(db_session, tag_data)
        
        assert tag1 == tag2
    
    def test_get_tag(self, db_session, test_tag):
        """Test getting a tag by ID"""
        tag = crud.get_tag(db_session, test_tag.id)
        assert tag == test_tag
        
        # Test non-existent tag
        tag = crud.get_tag(db_session, 99999)
        assert tag is None
    
    def test_get_tag_by_name(self, db_session, test_tag):
        """Test getting a tag by name"""
        tag = crud.get_tag_by_name(db_session, test_tag.name)
        assert tag == test_tag
        
        # Test non-existent tag
        tag = crud.get_tag_by_name(db_session, "nonexistent")
        assert tag is None
    
    def test_get_tags(self, db_session, test_tag):
        """Test getting all tags"""
        tags = crud.get_tags(db_session)
        assert test_tag in tags
    
    def test_update_tag(self, db_session, test_tag):
        """Test updating a tag"""
        update_data = schemas.TagUpdate(name="updated-tag", color="#00ff00")
        updated_tag = crud.update_tag(db_session, test_tag.id, update_data)
        
        assert updated_tag.name == "updated-tag"
        assert updated_tag.color == "#00ff00"
        
        # Test non-existent tag
        updated_tag = crud.update_tag(db_session, 99999, update_data)
        assert updated_tag is None
    
    def test_delete_tag(self, db_session, test_tag):
        """Test deleting a tag"""
        success = crud.delete_tag(db_session, test_tag.id)
        assert success is True
        
        # Verify tag is deleted
        tag = crud.get_tag(db_session, test_tag.id)
        assert tag is None
        
        # Test deleting non-existent tag
        success = crud.delete_tag(db_session, 99999)
        assert success is False
    
    def test_create_tags_from_names(self, db_session):
        """Test creating tags from list of names"""
        tag_names = ["tag1", "tag2", "tag3"]
        tags = crud.create_tags_from_names(db_session, tag_names)
        
        assert len(tags) == 3
        assert all(tag.name in tag_names for tag in tags)


class TestMeetingCRUD:
    """Test meeting CRUD operations"""
    
    def test_create_meeting(self, db_session, test_user):
        """Test creating a meeting"""
        meeting_data = schemas.MeetingCreate(
            title="Test Meeting",
            description="Test description"
        )
        meeting = crud.create_meeting(db_session, meeting_data, test_user.id)
        
        assert meeting.title == "Test Meeting"
        assert meeting.description == "Test description"
        assert meeting.owner_id == test_user.id
        assert meeting.status == "scheduled"
    
    def test_create_meeting_with_tags(self, db_session, test_user, test_tag):
        """Test creating meeting with tags"""
        meeting_data = schemas.MeetingCreate(
            title="Test Meeting",
            description="Test description",
            tag_ids=[test_tag.id]
        )
        meeting = crud.create_meeting(db_session, meeting_data, test_user.id)
        
        assert test_tag in meeting.tags
    
    def test_get_meetings(self, db_session, test_user, test_meeting):
        """Test getting meetings"""
        meetings = crud.get_meetings(db_session, user_id=test_user.id)
        assert test_meeting in meetings
        
        # Test getting all meetings (no user filter)
        all_meetings = crud.get_meetings(db_session)
        assert test_meeting in all_meetings
    
    def test_get_meeting(self, db_session, test_meeting):
        """Test getting a meeting by ID"""
        meeting = crud.get_meeting(db_session, test_meeting.id)
        assert meeting == test_meeting
        
        # Test non-existent meeting
        meeting = crud.get_meeting(db_session, 99999)
        assert meeting is None
    
    def test_update_meeting(self, db_session, test_user, test_meeting):
        """Test updating a meeting"""
        update_data = schemas.MeetingUpdate(
            title="Updated Title",
            description="Updated description"
        )
        updated_meeting = crud.update_meeting(
            db_session, 
            test_meeting.id, 
            update_data, 
            test_user.id
        )
        
        assert updated_meeting.title == "Updated Title"
        assert updated_meeting.description == "Updated description"
    
    def test_delete_meeting(self, db_session, test_user, test_meeting):
        """Test deleting a meeting"""
        success = crud.delete_meeting(db_session, test_meeting.id, test_user.id)
        assert success is True
        
        # Verify meeting is deleted
        meeting = crud.get_meeting(db_session, test_meeting.id)
        assert meeting is None
    
    def test_add_tags_to_meeting(self, db_session, test_user, test_meeting):
        """Test adding tags to meeting"""
        tag_names = ["new-tag-1", "new-tag-2"]
        updated_meeting = crud.add_tags_to_meeting(
            db_session, 
            test_meeting.id, 
            tag_names, 
            test_user.id
        )
        
        assert len(updated_meeting.tags) == 2
        tag_names_in_meeting = [tag.name for tag in updated_meeting.tags]
        assert "new-tag-1" in tag_names_in_meeting
        assert "new-tag-2" in tag_names_in_meeting
    
    def test_mark_meeting_as_ended(self, db_session, test_user, test_meeting):
        """Test marking meeting as ended"""
        ended_meeting = crud.mark_meeting_as_ended(
            db_session, 
            test_meeting.id, 
            test_user.id
        )
        
        assert ended_meeting.is_ended is True
        assert ended_meeting.end_time is not None
        assert ended_meeting.status == "completed"
    
    def test_get_meeting_status(self, db_session, test_user, test_meeting):
        """Test getting meeting status"""
        status = crud.get_meeting_status(
            db_session, 
            test_meeting.id, 
            test_user.id
        )
        
        assert "status" in status
        assert "is_ended" in status
        assert "transcription_count" in status


class TestSummaryCRUD:
    """Test summary CRUD operations"""
    
    def test_create_summary(self, db_session, test_meeting):
        """Test creating a summary"""
        summary_data = schemas.SummaryCreate(
            meeting_id=test_meeting.id,
            content="This is a test summary"
        )
        summary = crud.create_summary(db_session, summary_data)
        
        assert summary.meeting_id == test_meeting.id
        assert summary.content == "This is a test summary"
    
    def test_get_meeting_summaries(self, db_session, test_meeting):
        """Test getting meeting summaries"""
        # Create summary first
        summary_data = schemas.SummaryCreate(
            meeting_id=test_meeting.id,
            content="Test summary"
        )
        summary = crud.create_summary(db_session, summary_data)
        
        summaries = crud.get_meeting_summaries(db_session, test_meeting.id)
        assert summary in summaries
    
    def test_get_latest_meeting_summary(self, db_session, test_meeting):
        """Test getting latest meeting summary"""
        # Create multiple summaries
        for i in range(3):
            summary_data = schemas.SummaryCreate(
                meeting_id=test_meeting.id,
                content=f"Summary {i}"
            )
            crud.create_summary(db_session, summary_data)
        
        latest_summary = crud.get_latest_meeting_summary(db_session, test_meeting.id)
        assert latest_summary.content == "Summary 2"


class TestUtilityFunctions:
    """Test utility functions in CRUD"""
    
    def test_is_admin(self):
        """Test is_admin function"""
        admin_user = models.User(user_type=models.UserType.ADMIN)
        normal_user = models.User(user_type=models.UserType.NORMAL)
        
        assert crud.is_admin(admin_user) is True
        assert crud.is_admin(normal_user) is False
    
    def test_can_create_meetings(self):
        """Test can_create_meetings function"""
        admin_user = models.User(user_type=models.UserType.ADMIN)
        normal_user = models.User(user_type=models.UserType.NORMAL)
        pro_user = models.User(user_type=models.UserType.PRO)
        pending_user = models.User(user_type=models.UserType.PENDING)
        
        assert crud.can_create_meetings(admin_user) is True
        assert crud.can_create_meetings(normal_user) is True
        assert crud.can_create_meetings(pro_user) is True
        assert crud.can_create_meetings(pending_user) is False 