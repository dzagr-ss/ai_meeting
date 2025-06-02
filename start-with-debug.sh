#!/bin/bash
set -e

echo "=== Railway Deployment Debug Script ==="
echo "Python version: $(python --version)"
echo "Environment: $NODE_ENV"
echo "Working directory: $(pwd)"

echo -e "\n=== System Information ==="
echo "OS: $(uname -a)"
echo "Available packages:"
dpkg -l | grep -E "(libmagic|file)" || echo "No libmagic packages found"

echo -e "\n=== File command test ==="
which file || echo "file command not found"
file --version || echo "file command not working"

echo -e "\n=== Python magic test ==="
python test-libmagic.py || echo "LibMagic test failed"

echo -e "\n=== Python Dependencies Check ==="
echo "Checking critical dependencies..."
python -c "import sys; print('Python executable:', sys.executable)"
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)" || echo "FastAPI import failed"
python -c "import uvicorn; print('Uvicorn version:', uvicorn.__version__)" || echo "Uvicorn import failed"
python -c "import starlette; print('Starlette version:', starlette.__version__)" || echo "Starlette import failed"
python -c "import itsdangerous; print('itsdangerous version:', itsdangerous.__version__)" || echo "itsdangerous import failed"
python -c "import pydantic; print('Pydantic version:', pydantic.__version__)" || echo "Pydantic import failed"
python -c "import sqlalchemy; print('SQLAlchemy version:', sqlalchemy.__version__)" || echo "SQLAlchemy import failed"

echo -e "\n=== Installed packages ==="
pip list | head -20

echo -e "\n=== Directory contents ==="
ls -la

echo -e "\n=== Environment Variables ==="
env | grep -E "(PATH|LD_LIBRARY_PATH|PYTHONPATH)" || echo "No relevant env vars found"

echo -e "\n=== Starting application ==="
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} 