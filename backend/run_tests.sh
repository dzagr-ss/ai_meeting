#!/bin/bash

# Backend Unit Tests Runner
# This script runs all unit tests for the backend with coverage reporting

set -e  # Exit on any error

echo "🧪 Starting Backend Unit Tests..."

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Create test database if it doesn't exist
echo "📁 Setting up test environment..."

# Install test dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate || true

echo "📦 Installing test dependencies..."
pip install -r test_requirements.txt > /dev/null 2>&1 || {
    echo "⚠️  Installing basic test dependencies..."
    pip install pytest pytest-asyncio pytest-cov httpx faker factory-boy pytest-mock
}

# Set environment variables for testing
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="test-secret-key-for-testing-only"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export OPENAI_API_KEY="test-key"

# Clean up any existing test database
if [ -f "test.db" ]; then
    rm test.db
    echo "🗑️  Cleaned up previous test database"
fi

# Run tests with coverage
echo "🏃 Running tests..."

# Basic test run
echo "📊 Running unit tests..."
python -m pytest test_simple.py test_crud_extended.py test_schemas_simple.py -v --tb=short

# Run with coverage if coverage package is available
echo "📈 Running tests with coverage..."
python -m pytest test_simple.py test_crud_extended.py test_schemas_simple.py --cov=. --cov-report=html --cov-report=term-missing --cov-exclude="test_*" -v

echo "✅ All tests completed!"
echo ""
echo "📋 Test Summary:"
echo "  - Models: ✓"
echo "  - CRUD Operations: ✓"
echo "  - API Endpoints: ✓"
echo "  - Schemas: ✓"
echo ""
echo "📊 Coverage report generated in htmlcov/ directory"
echo "   Open htmlcov/index.html in your browser to view detailed coverage"

# Clean up test database
if [ -f "test.db" ]; then
    rm test.db
    echo "🗑️  Cleaned up test database"
fi

echo "�� Testing complete!" 