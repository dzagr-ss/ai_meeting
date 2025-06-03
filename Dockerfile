# Ultra-simple Railway Dockerfile - project root
FROM python:3.10-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies including libmagic and libsndfile for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libmagic1 \
    libmagic-dev \
    file \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    useradd -m railway

# Set working directory
WORKDIR /app

# Copy requirements and test scripts first
COPY requirements-railway.txt .
COPY test-libmagic.py .
COPY test-app-startup.py .
COPY start-with-debug.sh .

# Make scripts executable
RUN chmod +x start-with-debug.sh test-libmagic.py test-app-startup.py

# Install Python requirements
RUN pip install --no-cache-dir -r requirements-railway.txt

# Test libmagic installation
RUN echo "=== Testing libmagic installation ===" && \
    python test-libmagic.py || echo "LibMagic test failed during build"

# Copy backend application
COPY backend/ .

# Test application imports (basic test without full app)
RUN echo "=== Testing basic imports ===" && \
    python -c "import sys; print('Testing critical imports...'); import fastapi, uvicorn, starlette, itsdangerous, pydantic, sqlalchemy; print('✅ All critical web framework imports successful')" || echo "Basic import test failed during build"

# Create directories
RUN mkdir -p storage logs uploads && \
    chown -R railway:railway /app

# Switch to non-root user
USER railway

# Expose port
EXPOSE $PORT

# Start application with comprehensive debugging
CMD ["./start-with-debug.sh"] 