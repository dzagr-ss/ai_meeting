# Railway-optimized Dockerfile
FROM python:3.10-slim as builder

# Set build arguments for Railway optimization
ARG DEBIAN_FRONTEND=noninteractive

# Install essential build dependencies with memory optimization
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1-dev \
    libffi-dev \
    curl \
    git \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from the correct path (Railway builds from root)
COPY backend/requirements.txt .

# Install Python dependencies with Railway optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --no-compile -r requirements.txt

# Production stage - minimal and optimized
FROM python:3.10-slim

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from backend directory
COPY backend/ .

# Create app user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /app/storage /app/logs /app/tmp /app/models && \
    chown -R appuser:appuser /app

USER appuser

# Railway-optimized environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

EXPOSE 8000

# Simple health check for Railway
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Railway startup command with PORT variable support
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]