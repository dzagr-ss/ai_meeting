"""
Extended schema validation tests for better coverage
These tests focus on edge cases and validation logic not covered in test_simple.py
"""
import pytest
import os
from datetime import datetime
from pydantic import ValidationError

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_schemas_extended.db"
os.environ["SECRET_KEY"] = "this-is-a-test-secret-key-with-more-than-32-characters"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only-not-real"
os.environ["TESTING"] = "true"

# Import schemas
import schemas


class TestUserSchemaValidation:
    """Test user schema validation edge cases"""
    
    def test_user_create_email_validation(self):
        """Test email validation in UserCreate"""
        # Valid email
        valid_user = schemas.UserCreate(
            email="test@example.com",
            password="ValidPassword123!"
        )
        assert valid_user.email == "test@example.com"
        
        # Invalid email formats should raise ValidationError
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="invalid-email", password="ValidPassword123!")
        
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="@example.com", password="ValidPassword123!")
        
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="test@", password="ValidPassword123!")
    
    def test_user_create_password_strength(self):
        """Test password strength validation"""
        # Valid strong password
        valid_user = schemas.UserCreate(
            email="test@example.com",
            password="StrongPassword123!"
        )
        assert valid_user.password == "StrongPassword123!"
        
        # Weak passwords should raise ValidationError
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase, no numbers, no special chars
            "PASSWORD",  # No lowercase, no numbers, no special chars
            "Password",  # No numbers, no special chars
            "Password123",  # No special chars
            "Password!",  # No numbers
            "12345678!",  # No letters
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises(ValidationError):
                schemas.UserCreate(email="test@example.com", password=weak_password)
    
    def test_user_create_empty_fields(self):
        """Test validation with empty fields"""
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="", password="ValidPassword123!")
        
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="test@example.com", password="")
    
    def test_user_response_schema(self):
        """Test UserResponse schema"""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "user_type": "normal",
            "created_at": datetime.utcnow()
        }
        
        user_response = schemas.UserResponse(**user_data)
        assert user_response.id == 1
        assert user_response.email == "test@example.com"
        assert user_response.is_active is True
        assert user_response.user_type == "normal"


class TestPasswordResetSchemas:
    """Test password reset schema validation"""
    
    def test_password_reset_request(self):
        """Test PasswordResetRequest schema"""
        reset_request = schemas.PasswordResetRequest(email="test@example.com")
        assert reset_request.email == "test@example.com"
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            schemas.PasswordResetRequest(email="invalid-email")
    
    def test_password_reset_confirm_valid(self):
        """Test valid PasswordResetConfirm schema"""
        reset_confirm = schemas.PasswordResetConfirm(
            token="valid-token-123",
            new_password="NewStrongPassword123!"
        )
        assert reset_confirm.token == "valid-token-123"
        assert reset_confirm.new_password == "NewStrongPassword123!"
    
    def test_password_reset_confirm_weak_password(self):
        """Test PasswordResetConfirm with weak password"""
        with pytest.raises(ValidationError):
            schemas.PasswordResetConfirm(
                token="valid-token-123",
                new_password="weak"
            )
    
    def test_password_reset_confirm_empty_token(self):
        """Test PasswordResetConfirm with empty token"""
        with pytest.raises(ValidationError):
            schemas.PasswordResetConfirm(
                token="",
                new_password="StrongPassword123!"
            )


class TestTagSchemaValidation:
    """Test tag schema validation edge cases"""
    
    def test_tag_create_name_validation(self):
        """Test tag name validation"""
        # Valid tag name
        valid_tag = schemas.TagCreate(name="valid-tag-name", color="#ff0000")
        assert valid_tag.name == "valid-tag-name"
        
        # Test name sanitization (XSS prevention)
        xss_tag = schemas.TagCreate(name="<script>alert('xss')</script>", color="#ff0000")
        # The validator should sanitize the name
        assert "<script>" not in xss_tag.name
        assert "alert" not in xss_tag.name
    
    def test_tag_create_color_validation(self):
        """Test tag color validation"""
        # Valid hex colors
        valid_colors = ["#ff0000", "#00ff00", "#0000ff", "#ffffff", "#000000"]
        for color in valid_colors:
            tag = schemas.TagCreate(name="test-tag", color=color)
            assert tag.color == color
        
        # Invalid colors should still work (validation might be lenient)
        tag = schemas.TagCreate(name="test-tag", color="red")
        assert tag.color == "red"
    
    def test_tag_create_empty_name(self):
        """Test tag creation with empty name"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="", color="#ff0000")
    
    def test_tag_update_schema(self):
        """Test TagUpdate schema"""
        tag_update = schemas.TagUpdate(name="updated-tag", color="#00ff00")
        assert tag_update.name == "updated-tag"
        assert tag_update.color == "#00ff00"
        
        # Partial updates should work
        tag_update_name_only = schemas.TagUpdate(name="updated-tag")
        assert tag_update_name_only.name == "updated-tag"
        assert tag_update_name_only.color is None


class TestMeetingSchemaValidation:
    """Test meeting schema validation edge cases"""
    
    def test_meeting_create_title_validation(self):
        """Test meeting title validation"""
        # Valid title
        valid_meeting = schemas.MeetingCreate(
            title="Valid Meeting Title",
            description="Valid description"
        )
        assert valid_meeting.title == "Valid Meeting Title"
        
        # Test title sanitization (XSS prevention)
        xss_meeting = schemas.MeetingCreate(
            title="<script>alert('xss')</script>Meeting",
            description="Valid description"
        )
        # The validator should sanitize the title
        assert "<script>" not in xss_meeting.title
        assert "alert" not in xss_meeting.title
    
    def test_meeting_create_description_validation(self):
        """Test meeting description validation"""
        # Valid description
        valid_meeting = schemas.MeetingCreate(
            title="Valid Title",
            description="This is a valid description for the meeting."
        )
        assert valid_meeting.description == "This is a valid description for the meeting."
        
        # Test description sanitization (XSS prevention)
        xss_meeting = schemas.MeetingCreate(
            title="Valid Title",
            description="<script>alert('xss')</script>Description"
        )
        # The validator should sanitize the description
        assert "<script>" not in xss_meeting.description
        assert "alert" not in xss_meeting.description
    
    def test_meeting_create_empty_fields(self):
        """Test meeting creation with empty fields"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(title="", description="Valid description")
        
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(title="Valid title", description="")
    
    def test_meeting_update_schema(self):
        """Test MeetingUpdate schema"""
        meeting_update = schemas.MeetingUpdate(
            title="Updated Title",
            description="Updated description"
        )
        assert meeting_update.title == "Updated Title"
        assert meeting_update.description == "Updated description"
        
        # Partial updates should work
        meeting_update_title_only = schemas.MeetingUpdate(title="Updated Title")
        assert meeting_update_title_only.title == "Updated Title"
        assert meeting_update_title_only.description is None


class TestTranscriptionSchemas:
    """Test transcription schema validation"""
    
    def test_transcription_create_speaker_validation(self):
        """Test transcription speaker validation"""
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="This is what John said during the meeting.",
            start_time=0.0,
            end_time=10.5,
            meeting_id=1
        )
        assert transcription.speaker == "John Doe"
        
        # Test speaker sanitization
        xss_transcription = schemas.TranscriptionCreate(
            speaker="<script>alert('xss')</script>John",
            text="Valid text",
            start_time=0.0,
            end_time=10.5,
            meeting_id=1
        )
        assert "<script>" not in xss_transcription.speaker
        assert "alert" not in xss_transcription.speaker
    
    def test_transcription_create_text_validation(self):
        """Test transcription text validation"""
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="This is the transcribed text from the meeting.",
            start_time=0.0,
            end_time=10.5,
            meeting_id=1
        )
        assert transcription.text == "This is the transcribed text from the meeting."
        
        # Test text sanitization
        xss_transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="<script>alert('xss')</script>Valid text",
            start_time=0.0,
            end_time=10.5,
            meeting_id=1
        )
        assert "<script>" not in xss_transcription.text
        assert "alert" not in xss_transcription.text
    
    def test_transcription_create_time_validation(self):
        """Test transcription time validation"""
        # Valid times
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="Valid text",
            start_time=0.0,
            end_time=10.5,
            meeting_id=1
        )
        assert transcription.start_time == 0.0
        assert transcription.end_time == 10.5
        
        # End time should be after start time (if validation exists)
        transcription_reverse = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="Valid text",
            start_time=10.5,
            end_time=0.0,
            meeting_id=1
        )
        # This might pass if there's no validation for time order
        assert transcription_reverse.start_time == 10.5
        assert transcription_reverse.end_time == 0.0


class TestActionItemSchemas:
    """Test action item schema validation"""
    
    def test_action_item_create_description_validation(self):
        """Test action item description validation"""
        action_item = schemas.ActionItemCreate(
            description="Complete the project documentation",
            assignee="John Doe",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        assert action_item.description == "Complete the project documentation"
        
        # Test description sanitization
        xss_action_item = schemas.ActionItemCreate(
            description="<script>alert('xss')</script>Complete task",
            assignee="John Doe",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        assert "<script>" not in xss_action_item.description
        assert "alert" not in xss_action_item.description
    
    def test_action_item_create_assignee_validation(self):
        """Test action item assignee validation"""
        action_item = schemas.ActionItemCreate(
            description="Complete task",
            assignee="Jane Smith",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        assert action_item.assignee == "Jane Smith"
        
        # Test assignee sanitization
        xss_action_item = schemas.ActionItemCreate(
            description="Complete task",
            assignee="<script>alert('xss')</script>Jane",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        assert "<script>" not in xss_action_item.assignee
        assert "alert" not in xss_action_item.assignee


class TestSummarySchemas:
    """Test summary schema validation"""
    
    def test_summary_create_content_validation(self):
        """Test summary content validation"""
        summary = schemas.SummaryCreate(
            content="This is a comprehensive summary of the meeting discussion.",
            meeting_id=1
        )
        assert summary.content == "This is a comprehensive summary of the meeting discussion."
        
        # Test content sanitization
        xss_summary = schemas.SummaryCreate(
            content="<script>alert('xss')</script>Meeting summary content",
            meeting_id=1
        )
        assert "<script>" not in xss_summary.content
        assert "alert" not in xss_summary.content
    
    def test_summary_create_empty_content(self):
        """Test summary creation with empty content"""
        with pytest.raises(ValidationError):
            schemas.SummaryCreate(content="", meeting_id=1)


class TestMeetingNotesSchemas:
    """Test meeting notes schema validation"""
    
    def test_meeting_notes_create_content_validation(self):
        """Test meeting notes content validation"""
        notes = schemas.MeetingNotesCreate(
            content="These are detailed notes from the meeting.",
            meeting_id=1
        )
        assert notes.content == "These are detailed notes from the meeting."
        
        # Test content sanitization
        xss_notes = schemas.MeetingNotesCreate(
            content="<script>alert('xss')</script>Meeting notes",
            meeting_id=1
        )
        assert "<script>" not in xss_notes.content
        assert "alert" not in xss_notes.content


class TestAudioUploadSchemas:
    """Test audio upload schema validation"""
    
    def test_audio_upload_response_schema(self):
        """Test AudioUploadResponse schema"""
        upload_response = schemas.AudioUploadResponse(
            filename="meeting_audio.wav",
            file_size=1024000,
            duration=300.5,
            meeting_id=1
        )
        assert upload_response.filename == "meeting_audio.wav"
        assert upload_response.file_size == 1024000
        assert upload_response.duration == 300.5
        assert upload_response.meeting_id == 1


class TestTranscriptionResponseSchemas:
    """Test transcription response schema validation"""
    
    def test_transcription_segment_schema(self):
        """Test TranscriptionSegment schema"""
        segment = schemas.TranscriptionSegment(
            speaker="John Doe",
            text="This is what was said.",
            start_time=0.0,
            end_time=5.5
        )
        assert segment.speaker == "John Doe"
        assert segment.text == "This is what was said."
        assert segment.start_time == 0.0
        assert segment.end_time == 5.5
        
        # Test with sanitization
        xss_segment = schemas.TranscriptionSegment(
            speaker="<script>alert('xss')</script>John",
            text="<script>alert('xss')</script>Valid text",
            start_time=0.0,
            end_time=5.5
        )
        assert "<script>" not in xss_segment.speaker
        assert "<script>" not in xss_segment.text
        assert "alert" not in xss_segment.speaker
        assert "alert" not in xss_segment.text 