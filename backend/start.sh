#!/bin/bash

echo "🚀 Starting Railway deployment..."

# Run database migrations
echo "📋 Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed! Exiting..."
    exit 1
fi

echo "✅ Migrations completed successfully"

# Start the application
echo "🎯 Starting the application..."
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 