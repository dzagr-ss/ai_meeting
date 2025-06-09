import pytest
from pydantic import ValidationError
from datetime import datetime

import schemas


class TestUserSchemas:
    """Test user-related schemas"""
    
    def test_user_create_valid(self):
        """Test valid user creation"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        user = schemas.UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.password == "TestPassword123!"
    
    def test_user_create_invalid_email(self):
        """Test invalid email validation"""
        with pytest.raises(ValidationError):
            schemas.UserCreate(
                email="invalid-email",
                password="TestPassword123!"
            )
    
    def test_user_create_weak_password(self):
        """Test weak password validation"""
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase  
            "NoNumbers!",  # No numbers
            "NoSpecialChar123"  # No special characters
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                schemas.UserCreate(
                    email="test@example.com",
                    password=password
                )
    
    def test_user_login_valid(self):
        """Test valid user login"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        login = schemas.UserLogin(**login_data)
        
        assert login.email == "test@example.com"
        assert login.password == "password123"


class TestPasswordResetSchemas:
    """Test password reset schemas"""
    
    def test_password_reset_request_valid(self):
        """Test valid password reset request"""
        reset_request = schemas.PasswordResetRequest(email="test@example.com")
        assert reset_request.email == "test@example.com"
    
    def test_password_reset_confirm_valid(self):
        """Test valid password reset confirmation"""
        reset_confirm = schemas.PasswordResetConfirm(
            token="valid-token-123",
            new_password="NewPassword123!"
        )
        
        assert reset_confirm.token == "valid-token-123"
        assert reset_confirm.new_password == "NewPassword123!"
    
    def test_password_reset_confirm_invalid_token(self):
        """Test invalid token format"""
        with pytest.raises(ValidationError):
            schemas.PasswordResetConfirm(
                token="invalid token with spaces!",
                new_password="NewPassword123!"
            )
    
    def test_password_reset_confirm_weak_password(self):
        """Test weak password in reset confirmation"""
        with pytest.raises(ValidationError):
            schemas.PasswordResetConfirm(
                token="valid-token-123",
                new_password="weak"
            )


class TestTagSchemas:
    """Test tag schemas"""
    
    def test_tag_create_valid(self):
        """Test valid tag creation"""
        tag_data = {
            "name": "Test Tag",
            "color": "#ff0000"
        }
        tag = schemas.TagCreate(**tag_data)
        
        assert tag.name == "test tag"  # Should be normalized to lowercase
        assert tag.color == "#ff0000"
    
    def test_tag_create_default_color(self):
        """Test tag creation with default color"""
        tag = schemas.TagCreate(name="Test Tag")
        assert tag.color == "#6366f1"
    
    def test_tag_create_invalid_color(self):
        """Test invalid color format"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(
                name="Test Tag",
                color="invalid-color"
            )
    
    def test_tag_create_empty_name(self):
        """Test empty tag name"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="")
    
    def test_tag_create_long_name(self):
        """Test tag name too long"""
        with pytest.raises(ValidationError):
            schemas.TagCreate(name="a" * 51)  # Max is 50
    
    def test_tag_update_valid(self):
        """Test valid tag update"""
        tag_update = schemas.TagUpdate(
            name="Updated Tag",
            color="#00ff00"
        )
        
        assert tag_update.name == "updated tag"
        assert tag_update.color == "#00ff00"
    
    def test_tag_update_partial(self):
        """Test partial tag update"""
        tag_update = schemas.TagUpdate(name="Updated Tag")
        
        assert tag_update.name == "updated tag"
        assert tag_update.color is None


class TestMeetingSchemas:
    """Test meeting schemas"""
    
    def test_meeting_create_valid(self):
        """Test valid meeting creation""" 
        meeting_data = {
            "title": "Test Meeting",
            "description": "This is a test meeting"
        }
        meeting = schemas.MeetingCreate(**meeting_data)
        
        assert meeting.title == "Test Meeting"
        assert meeting.description == "This is a test meeting"
        assert meeting.tag_ids == []
    
    def test_meeting_create_with_tags(self):
        """Test meeting creation with tags"""
        meeting_data = {
            "title": "Test Meeting",
            "description": "This is a test meeting",
            "tag_ids": [1, 2, 3]
        }
        meeting = schemas.MeetingCreate(**meeting_data)
        
        assert meeting.tag_ids == [1, 2, 3]
    
    def test_meeting_create_empty_title(self):
        """Test empty meeting title"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(title="")
    
    def test_meeting_create_long_title(self):
        """Test meeting title too long"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(title="a" * 201)  # Max is 200
    
    def test_meeting_create_long_description(self):
        """Test meeting description too long"""
        with pytest.raises(ValidationError):
            schemas.MeetingCreate(
                title="Test Meeting",
                description="a" * 1001  # Max is 1000
            )
    
    def test_meeting_update_valid(self):
        """Test valid meeting update"""
        meeting_update = schemas.MeetingUpdate(
            title="Updated Meeting",
            description="Updated description"
        )
        
        assert meeting_update.title == "Updated Meeting"
        assert meeting_update.description == "Updated description"
    
    def test_meeting_update_partial(self):
        """Test partial meeting update"""
        meeting_update = schemas.MeetingUpdate(title="Updated Meeting")
        
        assert meeting_update.title == "Updated Meeting"
        assert meeting_update.description is None


class TestTranscriptionSchemas:
    """Test transcription schemas"""
    
    def test_transcription_create_valid(self):
        """Test valid transcription creation"""
        transcription_data = {
            "meeting_id": 1,
            "speaker": "John Doe",
            "text": "This is a test transcription"
        }
        transcription = schemas.TranscriptionCreate(**transcription_data)
        
        assert transcription.meeting_id == 1
        assert transcription.speaker == "John Doe"
        assert transcription.text == "This is a test transcription"
    
    def test_transcription_create_invalid_meeting_id(self):
        """Test invalid meeting ID"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                meeting_id=0,  # Must be > 0
                speaker="John Doe",
                text="Test text"
            )
    
    def test_transcription_create_empty_speaker(self):
        """Test empty speaker name"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                meeting_id=1,
                speaker="",
                text="Test text"
            )
    
    def test_transcription_create_empty_text(self):
        """Test empty transcription text"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                meeting_id=1,
                speaker="John Doe",
                text=""
            )
    
    def test_transcription_create_long_speaker(self):
        """Test speaker name too long"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                meeting_id=1,
                speaker="a" * 101,  # Max is 100
                text="Test text"
            )
    
    def test_transcription_create_long_text(self):
        """Test transcription text too long"""
        with pytest.raises(ValidationError):
            schemas.TranscriptionCreate(
                meeting_id=1,
                speaker="John Doe",
                text="a" * 10001  # Max is 10000
            )


class TestSpeakerSchemas:
    """Test speaker-related schemas"""
    
    def test_speaker_segment_valid(self):
        """Test valid speaker segment"""
        segment_data = {
            "speaker": "Speaker 1",
            "start_time": 0.0,
            "end_time": 10.5,
            "text": "Hello, this is a test"
        }
        segment = schemas.SpeakerSegment(**segment_data)
        
        assert segment.speaker == "Speaker 1"
        assert segment.start_time == 0.0
        assert segment.end_time == 10.5
        assert segment.text == "Hello, this is a test"
    
    def test_speaker_segment_invalid_times(self):
        """Test invalid time values"""
        # Negative start time
        with pytest.raises(ValidationError):
            schemas.SpeakerSegment(
                speaker="Speaker 1",
                start_time=-1.0,
                end_time=10.0,
                text="Test text"
            )
        
        # End time before start time
        with pytest.raises(ValidationError):
            schemas.SpeakerSegment(
                speaker="Speaker 1",
                start_time=10.0,
                end_time=5.0,
                text="Test text"
            )
    
    def test_speaker_identification_response_valid(self):
        """Test valid speaker identification response"""
        segments = [
            {
                "speaker": "Speaker 1",
                "start_time": 0.0,
                "end_time": 5.0,
                "text": "Hello"
            },
            {
                "speaker": "Speaker 2", 
                "start_time": 5.0,
                "end_time": 10.0,
                "text": "Hi there"
            }
        ]
        
        response = schemas.SpeakerIdentificationResponse(
            segments=segments,
            total_speakers=2
        )
        
        assert len(response.segments) == 2
        assert response.total_speakers == 2
    
    def test_speaker_identification_response_too_many_speakers(self):
        """Test too many speakers"""
        with pytest.raises(ValidationError):
            schemas.SpeakerIdentificationResponse(
                segments=[],
                total_speakers=51  # Max is 50
            )


class TestAudioSchemas:
    """Test audio-related schemas"""
    
    def test_audio_data_valid(self):
        """Test valid audio data"""
        audio_data = schemas.AudioData(
            audio_content=b"fake_audio_data",
            format="wav",
            sample_rate=16000,
            channels=1
        )
        
        assert audio_data.audio_content == b"fake_audio_data"
        assert audio_data.format == "wav"
        assert audio_data.sample_rate == 16000
        assert audio_data.channels == 1
    
    def test_audio_data_invalid_format(self):
        """Test invalid audio format"""
        with pytest.raises(ValidationError):
            schemas.AudioData(
                audio_content=b"fake_audio_data",
                format="invalid"  # Must be wav, mp3, m4a, or flac
            )
    
    def test_audio_data_invalid_sample_rate(self):
        """Test invalid sample rate"""
        # Too low
        with pytest.raises(ValidationError):
            schemas.AudioData(
                audio_content=b"fake_audio_data",
                sample_rate=7000  # Min is 8000
            )
        
        # Too high
        with pytest.raises(ValidationError):
            schemas.AudioData(
                audio_content=b"fake_audio_data",
                sample_rate=50000  # Max is 48000
            )
    
    def test_audio_data_invalid_channels(self):
        """Test invalid channel count"""
        # Too few
        with pytest.raises(ValidationError):
            schemas.AudioData(
                audio_content=b"fake_audio_data",
                channels=0  # Min is 1
            )
        
        # Too many
        with pytest.raises(ValidationError):
            schemas.AudioData(
                audio_content=b"fake_audio_data",
                channels=3  # Max is 2
            )


class TestSecurityValidation:
    """Test security validation functions"""
    
    def test_sanitize_text(self):
        """Test text sanitization"""
        # HTML escaping
        result = schemas.sanitize_text("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        
        # Remove dangerous characters
        result = schemas.sanitize_text('test"with\'quotes<>')
        assert '"' not in result
        assert "'" not in result
        assert '<' not in result
        assert '>' not in result
    
    def test_validate_no_sql_injection_safe_text(self):
        """Test SQL injection validation with safe text"""
        safe_texts = [
            "This is a normal meeting description",
            "We discussed quarterly results and budget",
            "Action items: 1. Review documents 2. Schedule follow-up"
        ]
        
        for text in safe_texts:
            # Should not raise exception
            result = schemas.validate_no_sql_injection(text)
            assert result == text
    
    def test_validate_no_sql_injection_dangerous_text(self):
        """Test SQL injection validation with dangerous text"""
        dangerous_texts = [
            "SELECT * FROM users WHERE id = 1",
            "DROP TABLE meetings",
            "INSERT INTO users VALUES (1, 'hacker')",
            "UPDATE users SET password = 'hacked'",
            "DELETE FROM meetings WHERE id > 0",
            "1=1 OR '1'='1'",
            "'; DROP TABLE users; --"
        ]
        
        for text in dangerous_texts:
            with pytest.raises(ValueError, match="potentially dangerous content"):
                schemas.validate_no_sql_injection(text)


class TestActionItemSchemas:
    """Test action item schemas"""
    
    def test_action_item_create_valid(self):
        """Test valid action item creation"""
        action_item_data = {
            "meeting_id": 1,
            "description": "Complete the project documentation",
            "assignee": "John Doe"
        }
        action_item = schemas.ActionItemCreate(**action_item_data)
        
        assert action_item.meeting_id == 1
        assert action_item.description == "Complete the project documentation"
        assert action_item.assignee == "John Doe"
    
    def test_action_item_create_minimal(self):
        """Test action item with minimal data"""
        action_item = schemas.ActionItemCreate(
            meeting_id=1,
            description="Test task"
        )
        
        assert action_item.meeting_id == 1
        assert action_item.description == "Test task"
        assert action_item.assignee is None
        assert action_item.due_date is None


class TestSummarySchemas:
    """Test summary schemas"""
    
    def test_summary_create_valid(self):
        """Test valid summary creation"""
        summary_data = {
            "meeting_id": 1,
            "content": "This meeting covered quarterly results and next steps."
        }
        summary = schemas.SummaryCreate(**summary_data)
        
        assert summary.meeting_id == 1
        assert summary.content == "This meeting covered quarterly results and next steps."
    
    def test_summary_create_empty_content(self):
        """Test empty summary content"""
        with pytest.raises(ValidationError):
            schemas.SummaryCreate(
                meeting_id=1,
                content=""
            )


class TestMeetingNotesSchemas:
    """Test meeting notes schemas"""
    
    def test_meeting_notes_create_valid(self):
        """Test valid meeting notes creation"""
        notes_data = {
            "meeting_id": 1,
            "content": "Key discussion points and decisions made."
        }
        notes = schemas.MeetingNotesCreate(**notes_data)
        
        assert notes.meeting_id == 1
        assert notes.content == "Key discussion points and decisions made."
    
    def test_meeting_notes_create_empty_content(self):
        """Test empty meeting notes content"""
        with pytest.raises(ValidationError):
            schemas.MeetingNotesCreate(
                meeting_id=1,
                content=""
            ) 