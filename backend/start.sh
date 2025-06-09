#!/bin/bash

echo "🚀 Starting Railway deployment..."

# Run database migrations
echo "📋 Running database migrations..."
alembic upgrade head

# Check if migration failed due to columns already existing
if [ $? -ne 0 ]; then
    echo "⚠️  Migration failed, checking if it's due to existing columns..."
    
    # Try to fix migration state by stamping to latest revision
    echo "🔧 Attempting to fix migration state..."
    python fix_migration_state.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Migration state fixed successfully!"
    else
        echo "❌ Failed to fix migration state! Exiting..."
        exit 1
    fi
else
    echo "✅ Migrations completed successfully"
fi

# Start the application
echo "🎯 Starting the application..."
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 