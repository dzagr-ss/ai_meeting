#!/bin/bash

# Railway Deployment Fix Script
# Handles all possible deployment issues with multiple strategies

set -e

echo "🔧 Railway Deployment Fix Script"
echo "==============================="

# Function to test local Docker build
test_docker_build() {
    echo "📦 Testing Docker build locally..."
    cd backend
    
    if docker build -t railway-test -f Dockerfile . > build.log 2>&1; then
        echo "✅ Docker build successful"
        docker images railway-test --format "Size: {{.Size}}"
        docker rmi railway-test
        return 0
    else
        echo "❌ Docker build failed"
        echo "Last 10 lines of build log:"
        tail -10 build.log
        return 1
    fi
    cd ..
}

# Function to test ultra-minimal requirements
test_minimal_requirements() {
    echo "🔬 Testing ultra-minimal requirements..."
    cd backend
    
    if python -m pip install --dry-run -r requirements-ultra-minimal.txt > /dev/null 2>&1; then
        echo "✅ Ultra-minimal requirements are installable"
        return 0
    else
        echo "❌ Issues with ultra-minimal requirements"
        return 1
    fi
    cd ..
}

# Function to create Railway deployment strategies
create_deployment_strategies() {
    echo "📋 Creating deployment strategies..."
    
    # Ensure backend directory exists
    mkdir -p backend
    
    # Strategy 1: Nixpacks (preferred)
    cat > .railway-strategy-1.toml << EOF
[build]
builder = "NIXPACKS"
nixpacksConfigPath = "backend/nixpacks.toml"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production.variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
ENVIRONMENT = "production"
STORAGE_PATH = "/app/storage"
PORT = "8000"
EOF

    # Strategy 2: Minimal Docker
    cat > .railway-strategy-2.toml << EOF
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile.railway"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production.variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
ENVIRONMENT = "production"
STORAGE_PATH = "/app/storage"
PORT = "8000"
EOF

    # Strategy 3: Ultra-minimal Docker
    cat > .railway-strategy-3.toml << EOF
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production.variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
ENVIRONMENT = "production"
STORAGE_PATH = "/app/storage"
PORT = "8000"
EOF

    echo "✅ Created 3 deployment strategies"
}

# Function to check file dependencies
check_files() {
    echo "📁 Checking required files..."
    
    files=(
        "backend/requirements-railway.txt"
        "backend/requirements-ultra-minimal.txt"
        "backend/Dockerfile"
        "backend/Dockerfile.railway"
        "backend/nixpacks.toml"
        "backend/main.py"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file exists"
        else
            echo "❌ $file missing"
            exit 1
        fi
    done
}

# Function to show deployment instructions
show_instructions() {
    echo ""
    echo "🚀 RAILWAY DEPLOYMENT INSTRUCTIONS"
    echo "=================================="
    echo ""
    echo "If you're still getting build errors, try these strategies in order:"
    echo ""
    echo "STRATEGY 1 (Recommended): Nixpacks"
    echo "- Copy content from .railway-strategy-1.toml to railway.toml"
    echo "- This avoids Docker registry issues entirely"
    echo ""
    echo "STRATEGY 2: Minimal Docker"
    echo "- Copy content from .railway-strategy-2.toml to railway.toml"
    echo "- Uses simplified Dockerfile.railway"
    echo ""
    echo "STRATEGY 3: Ultra-minimal fallback"
    echo "- Copy content from .railway-strategy-3.toml to railway.toml"
    echo "- Uses requirements-ultra-minimal.txt"
    echo ""
    echo "🔧 TROUBLESHOOTING SPECIFIC ERRORS:"
    echo ""
    echo "1. 'context canceled' or network timeouts:"
    echo "   → Use Strategy 1 (Nixpacks) - avoids Docker Hub entirely"
    echo ""
    echo "2. 'file not found' errors:"
    echo "   → Ensure you're in project root when deploying"
    echo "   → Check that files exist with: ls -la backend/"
    echo ""
    echo "3. 'image size exceeded' errors:"
    echo "   → Use Strategy 3 with ultra-minimal requirements"
    echo ""
    echo "4. Package installation failures:"
    echo "   → Remove google-generativeai and redis from requirements"
    echo "   → Add them back one by one to identify the problem"
    echo ""
    echo "📋 ENVIRONMENT VARIABLES TO SET IN RAILWAY:"
    echo "ENVIRONMENT=production"
    echo "DATABASE_URL=<auto-provided>"
    echo "SECRET_KEY=<generate-secure-key>"
    echo "OPENAI_API_KEY=<your-key>"
    echo "STORAGE_PATH=/app/storage"
    echo "PORT=8000"
    echo ""
    echo "🎯 QUICK FIX FOR YOUR CURRENT ERROR:"
    echo "Based on your error, try Strategy 1 (Nixpacks):"
    echo "cp .railway-strategy-1.toml railway.toml"
    echo "git add railway.toml && git commit -m 'fix: use nixpacks deployment' && git push"
    echo ""
}

# Main execution
main() {
    echo "Starting Railway deployment diagnostics..."
    
    check_files
    test_minimal_requirements
    create_deployment_strategies
    
    # Test Docker only if available
    if command -v docker &> /dev/null; then
        test_docker_build
    else
        echo "🔍 Docker not available for local testing"
    fi
    
    show_instructions
    
    echo ""
    echo "✅ Railway deployment fix script completed!"
    echo "Follow the strategies above based on your specific error."
}

main "$@" 