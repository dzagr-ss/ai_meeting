#!/bin/bash

# Backend startup script for stocks-agent
# This script properly activates the virtual environment and starts the backend

set -e  # Exit on any error

echo "Starting stocks-agent backend..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "Project root: $PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Error: Virtual environment not found at $PROJECT_ROOT/venv"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

# Verify activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated: $VIRTUAL_ENV"

# Change to backend directory
cd "$PROJECT_ROOT/backend"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in backend directory"
    exit 1
fi

# Start the backend
echo "Starting FastAPI backend..."
"$PROJECT_ROOT/venv/bin/python" main.py 