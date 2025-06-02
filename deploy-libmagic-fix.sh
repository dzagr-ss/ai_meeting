#!/bin/bash
set -e

echo "🔧 Deploying LibMagic Fix for Railway"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found. Please run from project root."
    exit 1
fi

echo "✅ Current directory contains Dockerfile"

# Make sure scripts are executable
echo "🔧 Making scripts executable..."
chmod +x start-with-debug.sh
chmod +x test-libmagic.py

echo "✅ Scripts made executable"

# Test the dockerfile locally if docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker found - you can test locally with:"
    echo "   docker build -t stocks-agent-test ."
    echo "   docker run -p 8000:8000 stocks-agent-test"
    echo ""
else
    echo "🔍 Docker not found - will test in Railway deployment"
fi

# Show what we've changed
echo "📋 Summary of changes made:"
echo "  1. Updated Dockerfile to install libmagic-dev and file packages"
echo "  2. Added build-essential for compilation"
echo "  3. Created test-libmagic.py to diagnose issues"
echo "  4. Created start-with-debug.sh for detailed logging"
echo "  5. Modified main.py to use lazy loading for magic module"
echo "  6. Fixed version pinning in requirements-railway.txt"

echo ""
echo "🚀 Ready to deploy! Push to Railway with:"
echo "   git add ."
echo "   git commit -m 'Fix libmagic import error in Railway deployment'"
echo "   git push"

echo ""
echo "📊 After deployment, check the Railway logs for:"
echo "  - LibMagic test results"
echo "  - System package information"
echo "  - Magic library status"
echo ""
echo "✨ The application should now start successfully!" 