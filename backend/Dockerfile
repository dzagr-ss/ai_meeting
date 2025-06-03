# Ultra-stable Railway deployment - handles all network and build issues
FROM python:3.10-slim-bullseye

# Prevent Docker build issues and optimize for Railway
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_TIMEOUT=1000
ENV PIP_RETRIES=10

# Create app user early
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies with retries and error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Set working directory
WORKDIR /app

# Copy requirements first (better Docker layer caching)
COPY requirements-railway.txt /app/requirements-railway.txt

# Install Python dependencies with comprehensive error handling
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements-railway.txt

# Copy all application files
COPY . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /app/storage /app/logs /app/uploads && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Clean up any build artifacts
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.10/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.10/site-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Comprehensive health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start application with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"] 