"""
Simple unit tests for core backend functionality
These tests avoid heavy dependencies and focus on core business logic
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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
    
    def test_tag_default_color(self, db_session):
        """Test tag default color"""
        tag = models.Tag(name="test-tag")
        db_session.add(tag)
        db_session.commit()
        
        assert tag.color == "#6366f1"


class TestMeetingModel:
    """Test Meeting model"""
    
    def test_create_meeting(self, db_session):
        """Test creating a meeting"""
        # First create a user
        user = models.User(
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Then create a meeting
        meeting = models.Meeting(
            title="Test Meeting",
            description="Test description",
            owner_id=user.id
        )
        db_session.add(meeting)
        db_session.commit()
        
        assert meeting.id is not None
        assert meeting.title == "Test Meeting"
        assert meeting.description == "Test description"
        assert meeting.owner_id == user.id
        assert meeting.status == "scheduled"
        assert meeting.is_ended is False
        assert meeting.start_time is not None


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
    
    def test_get_user_by_email(self, db_session):
        """Test getting a user by email"""
        # Create user first
        user_data = schemas.UserCreate(
            email="test2@example.com",
            password="TestPassword123!"
        )
        created_user = crud.create_user(db_session, user_data)
        
        # Get user by email
        user = crud.get_user_by_email(db_session, "test2@example.com")
        assert user == created_user
        
        # Test non-existent email
        user = crud.get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None
    
    def test_authenticate_user(self, db_session):
        """Test user authentication"""
        # Create user first
        user_data = schemas.UserCreate(
            email="test3@example.com",
            password="TestPassword123!"
        )
        user = crud.create_user(db_session, user_data)
        
        # Test correct password
        authenticated_user = crud.authenticate_user(
            db_session, 
            "test3@example.com", 
            "TestPassword123!"
        )
        assert authenticated_user == user
        
        # Test wrong password
        authenticated_user = crud.authenticate_user(
            db_session, 
            "test3@example.com", 
            "wrong_password"
        )
        assert authenticated_user is False


class TestSchemas:
    """Test Pydantic schemas"""
    
    def test_user_create_valid(self):
        """Test valid user creation"""
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        user = schemas.UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.password == "TestPassword123!"
    
    def test_user_create_weak_password(self):
        """Test weak password validation"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            schemas.UserCreate(
                email="test@example.com",
                password="weak"  # Too weak
            )
    
    def test_tag_create_valid(self):
        """Test valid tag creation"""
        tag_data = {
            "name": "Test Tag",
            "color": "#ff0000"
        }
        tag = schemas.TagCreate(**tag_data)
        
        assert tag.name == "test tag"  # Should be normalized to lowercase
        assert tag.color == "#ff0000"
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 