# Backend Unit Tests

This directory contains comprehensive unit tests for the backend API.

## Test Structure

### Test Files

- `conftest.py` - Pytest configuration and shared fixtures
- `test_models.py` - Database model tests
- `test_crud.py` - CRUD operation tests  
- `test_schemas.py` - Pydantic schema validation tests
- `test_api.py` - FastAPI endpoint tests
- `test_requirements.txt` - Testing dependencies
- `pytest.ini` - Pytest configuration
- `run_tests.sh` - Test runner script

### Test Coverage

The test suite covers:

#### 🗄️ **Database Models** (`test_models.py`)
- User model creation and constraints
- Meeting, Tag, Transcription relationships
- Password reset tokens
- Action items and summaries
- Database integrity constraints

#### 🔄 **CRUD Operations** (`test_crud.py`)
- User authentication and management
- Password reset functionality
- Meeting CRUD operations
- Tag management
- Summary and notes creation
- Admin functions

#### 📋 **Schema Validation** (`test_schemas.py`)
- Input validation and sanitization
- Password strength requirements
- Email format validation
- Security validation (XSS, SQL injection prevention)
- Data type constraints

#### 🌐 **API Endpoints** (`test_api.py`)
- Authentication and authorization
- Meeting management endpoints
- Tag operations
- Audio upload and transcription
- Admin-only endpoints
- Error handling and rate limiting

## Running Tests

### Quick Start

```bash
# Make sure you're in the backend directory
cd backend

# Run all tests
./run_tests.sh
```

### Manual Testing

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Set environment variables
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test-secret-key"

# Run specific test files
python -m pytest test_models.py -v
python -m pytest test_crud.py -v
python -m pytest test_schemas.py -v
python -m pytest test_api.py -v

# Run with coverage
python -m pytest test_*.py --cov=. --cov-report=html --cov-report=term-missing
```

### Test Options

```bash
# Run only unit tests (fast)
python -m pytest test_models.py test_crud.py test_schemas.py -v

# Run only API tests
python -m pytest test_api.py -v

# Run tests with detailed output
python -m pytest -v --tb=long

# Run specific test class
python -m pytest test_models.py::TestUserModel -v

# Run specific test method
python -m pytest test_api.py::TestUserEndpoints::test_create_user_success -v
```

## Test Environment

The tests use:
- **SQLite in-memory database** for fast, isolated testing
- **Mock objects** for external dependencies (email, OpenAI, etc.)
- **Test fixtures** for consistent test data
- **FastAPI TestClient** for API endpoint testing

## Key Features Tested

### Security
- ✅ Password hashing and validation
- ✅ JWT token authentication
- ✅ Input sanitization (XSS prevention)
- ✅ SQL injection prevention
- ✅ Rate limiting
- ✅ Admin authorization

### Functionality
- ✅ User registration and login
- ✅ Password reset flow
- ✅ Meeting CRUD operations
- ✅ Tag management
- ✅ Audio file upload validation
- ✅ Database relationships
- ✅ Error handling

### Data Validation
- ✅ Email format validation
- ✅ Password strength requirements
- ✅ Input length limits
- ✅ Data type validation
- ✅ Required field validation

## Coverage Goals

The test suite aims for:
- **>90% code coverage** on core functionality
- **100% coverage** on security-critical code
- **Edge case testing** for validation and error handling
- **Integration testing** for API endpoints

## Adding New Tests

When adding new features:

1. **Add model tests** in `test_models.py`
2. **Add CRUD tests** in `test_crud.py`  
3. **Add schema tests** in `test_schemas.py`
4. **Add API tests** in `test_api.py`
5. **Update fixtures** in `conftest.py` if needed

### Test Naming Convention

```python
def test_{feature}_{scenario}(self, fixtures):
    """Test description"""
    # Arrange
    # Act  
    # Assert
```

### Example Test

```python
def test_create_user_success(self, client):
    """Test successful user creation"""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }
    
    # Act
    response = client.post("/users/", json=user_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- Fast execution (< 30 seconds)
- No external dependencies
- Predictable and repeatable
- Clear failure messages

## Troubleshooting

### Common Issues

**Tests fail with database errors:**
```bash
# Clean up test database
rm test.db
```

**Import errors:**
```bash
# Install dependencies
pip install -r test_requirements.txt
```

**Permission errors:**
```bash
# Make script executable
chmod +x run_tests.sh
```

**Environment issues:**
```bash
# Set test environment variables
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
``` 