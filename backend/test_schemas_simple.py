"""
Simple schema validation tests that work with existing schemas
These tests focus on validation logic without testing non-existent schemas
"""
import pytest
import os
from datetime import datetime
from pydantic import ValidationError

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_schemas_simple.db"
os.environ["SECRET_KEY"] = "this-is-a-test-secret-key-with-more-than-32-characters"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only-not-real"
os.environ["TESTING"] = "true"

# Import schemas
import schemas


class TestUserSchemaValidation:
    """Test user schema validation"""
    
    def test_user_create_valid(self):
        """Test valid user creation"""
        user = schemas.UserCreate(
            email="test@example.com",
            password="ValidPassword123!"
        )
        assert user.email == "test@example.com"
        assert user.password == "ValidPassword123!"
    
    def test_user_create_invalid_email(self):
        """Test invalid email validation"""
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="invalid-email", password="ValidPassword123!")
    
    def test_user_create_weak_password(self):
        """Test weak password validation"""
        with pytest.raises(ValidationError):
            schemas.UserCreate(email="test@example.com", password="weak")
    
    def test_password_reset_request(self):
        """Test password reset request validation"""
        request = schemas.PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"
    
    def test_password_reset_confirm(self):
        """Test password reset confirm validation"""
        confirm = schemas.PasswordResetConfirm(
            token="valid-token",
            new_password="StrongPassword123!"
        )
        assert confirm.token == "valid-token"
        assert confirm.new_password == "StrongPassword123!"


class TestTagSchemaValidation:
    """Test tag schema validation"""
    
    def test_tag_create_valid(self):
        """Test valid tag creation"""
        tag = schemas.TagCreate(name="valid-tag", color="#ff0000")
        assert tag.name == "valid-tag"
        assert tag.color == "#ff0000"
    
    def test_tag_create_xss_prevention(self):
        """Test XSS prevention in tag names"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="<script>alert('xss')</script>", color="#ff0000")
    
    def test_tag_create_invalid_color(self):
        """Test invalid color format validation"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="test-tag", color="invalid-color")
    
    def test_tag_create_empty_name(self):
        """Test empty tag name validation"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="", color="#ff0000")
    
    def test_tag_update_partial(self):
        """Test partial tag updates"""
        update = schemas.TagUpdate(name="updated-tag")
        assert update.name == "updated-tag"
        assert update.color is None


class TestMeetingSchemaValidation:
    """Test meeting schema validation"""
    
    def test_meeting_create_valid(self):
        """Test valid meeting creation"""
        meeting = schemas.MeetingCreate(
            title="Valid Meeting",
            description="Valid description"
        )
        assert meeting.title == "Valid Meeting"
        assert meeting.description == "Valid description"
    
    def test_meeting_create_xss_prevention(self):
        """Test XSS prevention in meeting titles"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(
                title="<script>alert('xss')</script>",
                description="Valid description"
            )
    
    def test_meeting_create_empty_title(self):
        """Test empty title validation"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(title="", description="Valid description")
    
    def test_meeting_update_partial(self):
        """Test partial meeting updates"""
        update = schemas.MeetingUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.description is None


class TestTranscriptionSchemaValidation:
    """Test transcription schema validation"""
    
    def test_transcription_create_valid(self):
        """Test valid transcription creation"""
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="This is valid text",
            meeting_id=1
        )
        assert transcription.speaker == "John Doe"
        assert transcription.text == "This is valid text"
        assert transcription.meeting_id == 1
    
    def test_transcription_create_xss_prevention(self):
        """Test XSS prevention in transcription speaker"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                speaker="<script>alert('xss')</script>",
                text="Valid text",
                meeting_id=1
            )
    
    def test_transcription_text_sanitization(self):
        """Test text sanitization (should encode HTML)"""
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="<script>alert('xss')</script>Valid text",
            meeting_id=1
        )
        # The text should be HTML encoded
        assert "&lt;script&gt;" in transcription.text
        assert "alert" in transcription.text  # Still present but encoded
        assert "<script>" not in transcription.text  # Raw script tag removed


class TestActionItemSchemaValidation:
    """Test action item schema validation"""
    
    def test_action_item_create_valid(self):
        """Test valid action item creation"""
        action_item = schemas.ActionItemCreate(
            description="Complete the task",
            assignee="John Doe",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        assert action_item.description == "Complete the task"
        assert action_item.assignee == "John Doe"
        assert action_item.meeting_id == 1
    
    def test_action_item_description_sanitization(self):
        """Test description sanitization (should encode HTML)"""
        action_item = schemas.ActionItemCreate(
            description="<script>alert('xss')</script>Complete task",
            assignee="John Doe",
            due_date=datetime.utcnow(),
            meeting_id=1
        )
        # The description should be HTML encoded
        assert "&lt;script&gt;" in action_item.description
        assert "alert" in action_item.description  # Still present but encoded
        assert "<script>" not in action_item.description  # Raw script tag removed
    
    def test_action_item_xss_prevention_assignee(self):
        """Test XSS prevention in assignee field"""
        with pytest.raises(ValidationError):
            schemas.ActionItemCreate(
                description="Valid description",
                assignee="<script>alert('xss')</script>",
                due_date=datetime.utcnow(),
                meeting_id=1
            )


class TestSummarySchemaValidation:
    """Test summary schema validation"""
    
    def test_summary_create_valid(self):
        """Test valid summary creation"""
        summary = schemas.SummaryCreate(
            content="This is a valid summary.",
            meeting_id=1
        )
        assert summary.content == "This is a valid summary."
        assert summary.meeting_id == 1
    
    def test_summary_content_sanitization(self):
        """Test content sanitization (should encode HTML)"""
        summary = schemas.SummaryCreate(
            content="<script>alert('xss')</script>Summary content",
            meeting_id=1
        )
        # The content should be HTML encoded
        assert "&lt;script&gt;" in summary.content
        assert "alert" in summary.content  # Still present but encoded
        assert "<script>" not in summary.content  # Raw script tag removed
    
    def test_summary_empty_content(self):
        """Test empty content validation"""
        with pytest.raises(ValidationError):
            schemas.SummaryCreate(content="", meeting_id=1)


class TestMeetingNotesSchemaValidation:
    """Test meeting notes schema validation"""
    
    def test_meeting_notes_create_valid(self):
        """Test valid meeting notes creation"""
        notes = schemas.MeetingNotesCreate(
            content="These are valid meeting notes.",
            meeting_id=1
        )
        assert notes.content == "These are valid meeting notes."
        assert notes.meeting_id == 1
    
    def test_meeting_notes_content_sanitization(self):
        """Test content sanitization (should encode HTML)"""
        notes = schemas.MeetingNotesCreate(
            content="<script>alert('xss')</script>Meeting notes",
            meeting_id=1
        )
        # The content should be HTML encoded
        assert "&lt;script&gt;" in notes.content
        assert "alert" in notes.content  # Still present but encoded
        assert "<script>" not in notes.content  # Raw script tag removed


class TestSecurityValidation:
    """Test security validation features"""
    
    def test_xss_prevention_blocks_script_tags(self):
        """Test that script tags are blocked in sensitive fields"""
        # These should raise ValidationError
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="<script>alert('xss')</script>", color="#ff0000")
        
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(
                title="<script>alert('xss')</script>",
                description="Valid description"
            )
        
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                speaker="<script>alert('xss')</script>",
                text="Valid text",
                meeting_id=1
            )
    
    def test_html_content_sanitized_not_blocked(self):
        """Test that HTML content is sanitized but not blocked in text fields"""
        # These should succeed but sanitize the content
        transcription = schemas.TranscriptionCreate(
            speaker="John Doe",
            text="<b>Bold text</b> and <script>alert('xss')</script>",
            meeting_id=1
        )
        assert "&lt;b&gt;" in transcription.text or "<b>" not in transcription.text
        
        summary = schemas.SummaryCreate(
            content="<p>Paragraph</p> and <script>alert('xss')</script>",
            meeting_id=1
        )
        assert "&lt;p&gt;" in summary.content or "<p>" not in summary.content
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        # Test that SQL injection attempts are blocked by validation
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(
                title="Meeting'; DROP TABLE meetings; --",
                description="Valid description"
            )
        
        # Test SQL injection in text fields that are sanitized (not blocked completely)
        summary = schemas.SummaryCreate(
            content="Summary with some SQL: SELECT * FROM users",
            meeting_id=1
        )
        # Should just be treated as literal content (less dangerous SQL)
        assert "SELECT" in summary.content


class TestPasswordValidation:
    """Test password validation logic"""
    
    def test_strong_passwords_accepted(self):
        """Test that strong passwords are accepted"""
        strong_passwords = [
            "MyStrongPassword123!",
            "Tr0ub4dor&3",
            "P@ssw0rd123",
            "ComplexPassword2023!",
        ]
        
        for password in strong_passwords:
            user = schemas.UserCreate(
                email="test@example.com",
                password=password
            )
            assert user.password == password
    
    def test_weak_passwords_rejected(self):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase, no numbers, no special chars
            "PASSWORD",  # No lowercase, no numbers, no special chars
            "Password",  # No numbers, no special chars
            "Password123",  # No special chars
            "Password!",  # No numbers
            "12345678!",  # No letters
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                schemas.UserCreate(email="test@example.com", password=password) 