# Ultra-simple Railway Dockerfile - project root
FROM python:3.10-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies including libmagic for python-magic
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    useradd -m railway

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy backend application
COPY backend/ .

# Create directories
RUN mkdir -p storage logs uploads && \
    chown -R railway:railway /app

# Switch to non-root user
USER railway

# Expose port
EXPOSE $PORT

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 