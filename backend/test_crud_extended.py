"""
Extended CRUD tests for better coverage
These tests focus on CRUD operations not covered in test_simple.py
"""
import pytest
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_crud_extended.db"
os.environ["SECRET_KEY"] = "this-is-a-test-secret-key-with-more-than-32-characters"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only-not-real"
os.environ["TESTING"] = "true"

# Import core modules
import models
import schemas
import crud
from database import Base

# Create test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crud_extended.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a clean database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user_data = schemas.UserCreate(
        email="testuser@example.com",
        password="TestPassword123!"
    )
    return crud.create_user(db_session, user_data)


@pytest.fixture
def test_meeting(db_session, test_user):
    """Create a test meeting"""
    meeting_data = schemas.MeetingCreate(
        title="Test Meeting",
        description="Test meeting description"
    )
    return crud.create_meeting(db_session, meeting_data, test_user.id)


@pytest.fixture
def test_tag(db_session):
    """Create a test tag"""
    tag_data = schemas.TagCreate(
        name="test-tag",
        color="#ff0000"
    )
    return crud.create_tag(db_session, tag_data)


class TestPasswordResetCRUD:
    """Test password reset CRUD operations"""
    
    def test_create_password_reset_token(self, db_session, test_user):
        """Test creating a password reset token"""
        token = crud.create_password_reset_token(db_session, test_user.email)
        
        assert token is not None
        assert len(token) > 0
        
        # Verify token exists in database
        db_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.email == test_user.email
        ).first()
        assert db_token is not None
        assert db_token.token == token
    
    def test_validate_password_reset_token_valid(self, db_session, test_user):
        """Test validating a valid password reset token"""
        token = crud.create_password_reset_token(db_session, test_user.email)
        
        token_obj = crud.validate_password_reset_token(db_session, token)
        assert token_obj is not None
        assert token_obj.email == test_user.email
    
    def test_validate_password_reset_token_invalid(self, db_session):
        """Test validating an invalid password reset token"""
        token_obj = crud.validate_password_reset_token(db_session, "invalid-token")
        assert token_obj is None
    
    def test_validate_password_reset_token_expired(self, db_session, test_user):
        """Test validating an expired password reset token"""
        token = crud.create_password_reset_token(db_session, test_user.email)
        
        # Manually expire the token
        db_token = db_session.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == token
        ).first()
        db_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()
        
        token_obj = crud.validate_password_reset_token(db_session, token)
        assert token_obj is None
    
    def test_reset_password(self, db_session, test_user):
        """Test resetting a user's password"""
        token = crud.create_password_reset_token(db_session, test_user.email)
        new_password = "NewPassword123!"
        
        success = crud.reset_password(db_session, token, new_password)
        assert success is True
        
        # Verify password was changed
        updated_user = crud.authenticate_user(db_session, test_user.email, new_password)
        assert updated_user is not None
        assert updated_user.id == test_user.id


class TestMeetingCRUD:
    """Test meeting CRUD operations"""
    
    def test_get_meetings_with_user_id(self, db_session, test_user):
        """Test getting user's meetings"""
        # Create multiple meetings
        meeting1_data = schemas.MeetingCreate(title="Meeting 1", description="First meeting")
        meeting2_data = schemas.MeetingCreate(title="Meeting 2", description="Second meeting")
        
        meeting1 = crud.create_meeting(db_session, meeting1_data, test_user.id)
        meeting2 = crud.create_meeting(db_session, meeting2_data, test_user.id)
        
        meetings = crud.get_meetings(db_session, user_id=test_user.id)
        assert len(meetings) == 2
        meeting_ids = [m.id for m in meetings]
        assert meeting1.id in meeting_ids
        assert meeting2.id in meeting_ids
    
    def test_get_meetings_all(self, db_session, test_user):
        """Test getting all meetings without user filter"""
        # Create a meeting
        meeting_data = schemas.MeetingCreate(title="Meeting 1", description="First meeting")
        meeting = crud.create_meeting(db_session, meeting_data, test_user.id)
        
        meetings = crud.get_meetings(db_session)
        assert len(meetings) >= 1
        meeting_ids = [m.id for m in meetings]
        assert meeting.id in meeting_ids
    
    def test_get_meeting(self, db_session, test_meeting):
        """Test getting a specific meeting"""
        meeting = crud.get_meeting(db_session, test_meeting.id)
        assert meeting is not None
        assert meeting.id == test_meeting.id
        assert meeting.title == test_meeting.title
    
    def test_get_meeting_not_found(self, db_session):
        """Test getting a non-existent meeting"""
        meeting = crud.get_meeting(db_session, 99999)
        assert meeting is None
    
    def test_update_meeting(self, db_session, test_meeting, test_user):
        """Test updating a meeting"""
        update_data = schemas.MeetingUpdate(
            title="Updated Meeting Title",
            description="Updated description"
        )
        
        updated_meeting = crud.update_meeting(db_session, test_meeting.id, update_data, test_user.id)
        assert updated_meeting is not None
        assert updated_meeting.title == "Updated Meeting Title"
        assert updated_meeting.description == "Updated description"
    
    def test_delete_meeting(self, db_session, test_meeting, test_user):
        """Test deleting a meeting"""
        meeting_id = test_meeting.id
        
        success = crud.delete_meeting(db_session, meeting_id, test_user.id)
        assert success is True
        
        # Verify meeting was deleted
        deleted_meeting = crud.get_meeting(db_session, meeting_id)
        assert deleted_meeting is None
    
    def test_mark_meeting_as_ended(self, db_session, test_meeting, test_user):
        """Test marking a meeting as ended"""
        updated_meeting = crud.mark_meeting_as_ended(db_session, test_meeting.id, test_user.id)
        assert updated_meeting is not None
        
        # Verify meeting is marked as ended
        assert updated_meeting.is_ended is True
        assert updated_meeting.status == "completed"
    
    def test_get_meeting_status(self, db_session, test_meeting, test_user):
        """Test getting meeting status"""
        status = crud.get_meeting_status(db_session, test_meeting.id, test_user.id)
        assert status is not None
        assert "status" in status
        assert status["status"] == "scheduled"


class TestTagCRUD:
    """Test tag CRUD operations"""
    
    def test_get_tags(self, db_session):
        """Test getting all tags"""
        # Create multiple tags
        tag1_data = schemas.TagCreate(name="tag1", color="#ff0000")
        tag2_data = schemas.TagCreate(name="tag2", color="#00ff00")
        
        tag1 = crud.create_tag(db_session, tag1_data)
        tag2 = crud.create_tag(db_session, tag2_data)
        
        tags = crud.get_tags(db_session)
        assert len(tags) >= 2
        tag_names = [tag.name for tag in tags]
        assert "tag1" in tag_names
        assert "tag2" in tag_names
    
    def test_get_tag(self, db_session, test_tag):
        """Test getting a specific tag"""
        tag = crud.get_tag(db_session, test_tag.id)
        assert tag is not None
        assert tag.id == test_tag.id
        assert tag.name == test_tag.name
    
    def test_get_tag_by_name(self, db_session, test_tag):
        """Test getting a tag by name"""
        tag = crud.get_tag_by_name(db_session, test_tag.name)
        assert tag is not None
        assert tag.id == test_tag.id
        assert tag.name == test_tag.name
    
    def test_get_tag_by_name_not_found(self, db_session):
        """Test getting a non-existent tag by name"""
        tag = crud.get_tag_by_name(db_session, "non-existent-tag")
        assert tag is None
    
    def test_update_tag(self, db_session, test_tag):
        """Test updating a tag"""
        update_data = schemas.TagUpdate(
            name="updated-tag",
            color="#0000ff"
        )
        
        updated_tag = crud.update_tag(db_session, test_tag.id, update_data)
        assert updated_tag is not None
        assert updated_tag.name == "updated-tag"
        assert updated_tag.color == "#0000ff"
    
    def test_delete_tag(self, db_session, test_tag):
        """Test deleting a tag"""
        tag_id = test_tag.id
        
        success = crud.delete_tag(db_session, tag_id)
        assert success is True
        
        # Verify tag was deleted
        deleted_tag = crud.get_tag(db_session, tag_id)
        assert deleted_tag is None
    
    def test_create_tags_from_names(self, db_session):
        """Test creating multiple tags from names"""
        tag_names = ["tag-a", "tag-b", "tag-c"]
        tags = crud.create_tags_from_names(db_session, tag_names)
        
        assert len(tags) == 3
        created_names = [tag.name for tag in tags]
        for name in tag_names:
            assert name in created_names
    
    def test_add_tags_to_meeting(self, db_session, test_meeting, test_user):
        """Test adding tags to a meeting"""
        tag_names = ["urgent", "project-alpha"]
        
        updated_meeting = crud.add_tags_to_meeting(db_session, test_meeting.id, tag_names, test_user.id)
        assert updated_meeting is not None
        
        # Verify tags were added
        meeting_tag_names = [tag.name for tag in updated_meeting.tags]
        for name in tag_names:
            assert name in meeting_tag_names


class TestUserUtilities:
    """Test user utility functions"""
    
    def test_get_user(self, db_session, test_user):
        """Test getting a user by ID"""
        user = crud.get_user(db_session, test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    def test_get_user_not_found(self, db_session):
        """Test getting a non-existent user"""
        user = crud.get_user(db_session, 99999)
        assert user is None
    
    def test_get_all_users(self, db_session):
        """Test getting all users with pagination"""
        # Create multiple users
        user1_data = schemas.UserCreate(email="user1@example.com", password="Password123!")
        user2_data = schemas.UserCreate(email="user2@example.com", password="Password123!")
        
        crud.create_user(db_session, user1_data)
        crud.create_user(db_session, user2_data)
        
        users = crud.get_all_users(db_session, skip=0, limit=10)
        assert len(users) >= 2
        
        # Test pagination
        users_page1 = crud.get_all_users(db_session, skip=0, limit=1)
        users_page2 = crud.get_all_users(db_session, skip=1, limit=1)
        
        assert len(users_page1) == 1
        assert len(users_page2) >= 1
        assert users_page1[0].id != users_page2[0].id
    
    def test_update_user_type(self, db_session, test_user):
        """Test updating user type"""
        updated_user = crud.update_user_type(db_session, test_user.id, "pro")
        assert updated_user is not None
        
        # Verify user type was updated
        assert updated_user.user_type.value == "pro"
    
    def test_is_admin(self, db_session):
        """Test admin check function"""
        # Create admin user
        admin_data = schemas.UserCreate(
            email="zagravsky@gmail.com",
            password="AdminPassword123!"
        )
        admin_user = crud.create_user(db_session, admin_data)
        
        assert crud.is_admin(admin_user) is True
        
        # Create normal user
        normal_data = schemas.UserCreate(
            email="normal@example.com",
            password="Password123!"
        )
        normal_user = crud.create_user(db_session, normal_data)
        
        assert crud.is_admin(normal_user) is False
    
    def test_can_create_meetings(self, db_session):
        """Test meeting creation permission check"""
        # Create admin user
        admin_data = schemas.UserCreate(
            email="zagravsky@gmail.com",
            password="AdminPassword123!"
        )
        admin_user = crud.create_user(db_session, admin_data)
        
        assert crud.can_create_meetings(admin_user) is True
        
        # Create normal user
        normal_data = schemas.UserCreate(
            email="normal@example.com",
            password="Password123!"
        )
        normal_user = crud.create_user(db_session, normal_data)
        
        # Normal users should also be able to create meetings (based on the actual function logic)
        assert crud.can_create_meetings(normal_user) is False  # PENDING users cannot create meetings


class TestSummaryCRUD:
    """Test summary CRUD operations"""
    
    def test_create_summary(self, db_session, test_meeting):
        """Test creating a meeting summary"""
        summary_data = schemas.SummaryCreate(
            content="This is a test summary of the meeting.",
            meeting_id=test_meeting.id
        )
        
        summary = crud.create_summary(db_session, summary_data)
        assert summary is not None
        assert summary.content == "This is a test summary of the meeting."
        assert summary.meeting_id == test_meeting.id
    
    def test_get_meeting_summaries(self, db_session, test_meeting):
        """Test getting summaries by meeting ID"""
        # Create multiple summaries
        summary1_data = schemas.SummaryCreate(
            content="First summary",
            meeting_id=test_meeting.id
        )
        summary2_data = schemas.SummaryCreate(
            content="Second summary",
            meeting_id=test_meeting.id
        )
        
        crud.create_summary(db_session, summary1_data)
        crud.create_summary(db_session, summary2_data)
        
        summaries = crud.get_meeting_summaries(db_session, test_meeting.id)
        assert len(summaries) == 2
        summary_contents = [s.content for s in summaries]
        assert "First summary" in summary_contents
        assert "Second summary" in summary_contents
    
    def test_get_latest_meeting_summary(self, db_session, test_meeting):
        """Test getting the latest summary for a meeting"""
        # Create multiple summaries
        summary1_data = schemas.SummaryCreate(
            content="First summary",
            meeting_id=test_meeting.id
        )
        summary2_data = schemas.SummaryCreate(
            content="Latest summary",
            meeting_id=test_meeting.id
        )
        
        crud.create_summary(db_session, summary1_data)
        latest_summary = crud.create_summary(db_session, summary2_data)
        
        retrieved_summary = crud.get_latest_meeting_summary(db_session, test_meeting.id)
        assert retrieved_summary is not None
        assert retrieved_summary.content == "Latest summary"
        assert retrieved_summary.id == latest_summary.id


class TestMeetingNotesCRUD:
    """Test meeting notes CRUD operations"""
    
    def test_create_meeting_notes(self, db_session, test_meeting):
        """Test creating meeting notes"""
        notes_data = schemas.MeetingNotesCreate(
            content="These are detailed notes from the meeting.",
            meeting_id=test_meeting.id
        )
        
        notes = crud.create_meeting_notes(db_session, notes_data)
        assert notes is not None
        assert notes.content == "These are detailed notes from the meeting."
        assert notes.meeting_id == test_meeting.id
    
    def test_get_meeting_notes(self, db_session, test_meeting):
        """Test getting notes by meeting ID"""
        # Create multiple notes
        notes1_data = schemas.MeetingNotesCreate(
            content="First notes",
            meeting_id=test_meeting.id
        )
        notes2_data = schemas.MeetingNotesCreate(
            content="Second notes",
            meeting_id=test_meeting.id
        )
        
        crud.create_meeting_notes(db_session, notes1_data)
        crud.create_meeting_notes(db_session, notes2_data)
        
        notes_list = crud.get_meeting_notes(db_session, test_meeting.id)
        assert len(notes_list) == 2
        notes_contents = [n.content for n in notes_list]
        assert "First notes" in notes_contents
        assert "Second notes" in notes_contents
    
    def test_get_latest_meeting_notes(self, db_session, test_meeting):
        """Test getting the latest notes for a meeting"""
        # Create multiple notes
        notes1_data = schemas.MeetingNotesCreate(
            content="First notes",
            meeting_id=test_meeting.id
        )
        notes2_data = schemas.MeetingNotesCreate(
            content="Latest notes",
            meeting_id=test_meeting.id
        )
        
        crud.create_meeting_notes(db_session, notes1_data)
        latest_notes = crud.create_meeting_notes(db_session, notes2_data)
        
        retrieved_notes = crud.get_latest_meeting_notes(db_session, test_meeting.id)
        assert retrieved_notes is not None
        assert retrieved_notes.content == "Latest notes"
        assert retrieved_notes.id == latest_notes.id


class TestAccessTokenCRUD:
    """Test access token creation"""
    
    def test_create_access_token(self):
        """Test creating an access token"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = crud.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0 