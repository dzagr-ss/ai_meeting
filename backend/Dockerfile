# Optimized multi-stage build for Railway deployment
# Target: Under 4GB image size
FROM python:3.10-slim AS builder

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy production requirements
COPY requirements-production.txt .

# Install optimized dependencies with CPU-only PyTorch
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-production.txt

# Production stage - minimal runtime image
FROM python:3.10-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy only essential Python packages (selective copy to reduce size)
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Remove unnecessary files to reduce image size
RUN find /usr/local/lib/python3.10/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.10/site-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.10/site-packages -name "*.so" -exec strip {} + 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.10/site-packages/torch/test && \
    rm -rf /usr/local/lib/python3.10/site-packages/torch/include && \
    rm -rf /usr/local/lib/python3.10/site-packages/*/tests

# Copy application code
COPY . .

# Copy simplified speaker identification for production
COPY speaker_identification_simple.py speaker_identification.py

# Create necessary directories and set permissions
RUN mkdir -p /app/storage /app/logs && \
    chown -R appuser:appuser /app && \
    chmod +x /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTORCH_DISABLE_CUDA_MEMORY_ALLOCATOR=1

# Expose port
EXPOSE 8000

# Simple health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 