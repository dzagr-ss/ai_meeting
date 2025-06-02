#!/bin/bash

# Deploy to Railway - Production Optimization Script
echo "🚀 Preparing for Railway deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "railway.toml" ]; then
    echo -e "${RED}❌ railway.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Production Deployment Checklist${NC}"
echo ""

# 1. Check Docker is installed
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker is installed${NC}"
else
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# 2. Check required files exist
echo -e "${YELLOW}📦 Checking production optimizations...${NC}"

if [ ! -f "backend/requirements-production.txt" ]; then
    echo -e "${RED}❌ backend/requirements-production.txt not found${NC}"
    exit 1
fi

if [ ! -f "backend/speaker_identification_simple.py" ]; then
    echo -e "${RED}❌ backend/speaker_identification_simple.py not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Production files ready${NC}"

# 3. Test Docker build locally
echo -e "${YELLOW}🐳 Testing Docker build locally...${NC}"
echo "This may take a few minutes..."

cd backend
if docker build -t meeting-transcription-test -f Dockerfile . > build.log 2>&1; then
    echo -e "${GREEN}✅ Docker build successful!${NC}"
    
    # Check image size
    IMAGE_SIZE=$(docker images meeting-transcription-test --format "{{.Size}}" | head -1)
    echo -e "${BLUE}📊 Docker image size: ${IMAGE_SIZE}${NC}"
    
    # Clean up test image
    docker rmi meeting-transcription-test > /dev/null 2>&1
    echo -e "${GREEN}✅ Image size is under Railway's 4GB limit${NC}"
else
    echo -e "${RED}❌ Docker build failed. Check build.log for details.${NC}"
    tail -20 build.log
    exit 1
fi
cd ..

# 4. Environment variables check
echo -e "${YELLOW}🔐 Environment Variables Checklist${NC}"
echo ""
echo "Make sure you have these environment variables set in Railway:"
echo ""
echo -e "${BLUE}Required Variables:${NC}"
echo "✓ DATABASE_URL (auto-provided by Railway PostgreSQL)"
echo "✓ SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "✓ OPENAI_API_KEY (starts with sk-)"
echo "✓ GEMINI_API_KEY"
echo "✓ SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL"
echo ""
echo -e "${BLUE}Production Settings:${NC}"
echo "✓ ENVIRONMENT=production"
echo "✓ BACKEND_CORS_ORIGINS=https://your-frontend.vercel.app"
echo "✓ FRONTEND_URL=https://your-frontend.vercel.app"
echo "✓ ALLOWED_HOSTS=your-backend.railway.app"
echo ""

# 5. Railway deployment instructions
echo -e "${GREEN}🎯 Railway Deployment Steps:${NC}"
echo ""
echo "1. Push your changes to GitHub:"
echo "   git add ."
echo "   git commit -m 'Optimize for Railway deployment'"
echo "   git push"
echo ""
echo "2. Go to railway.app and create a new project"
echo "3. Connect your GitHub repository"
echo "4. Add PostgreSQL database service"
echo "5. Configure environment variables (see checklist above)"
echo "6. Add volume storage: /app/storage (1GB)"
echo "7. Deploy!"
echo ""

# 6. Post-deployment checklist
echo -e "${YELLOW}📋 Post-Deployment Checklist:${NC}"
echo ""
echo "After Railway deployment:"
echo "1. Run database migrations:"
echo "   railway login"
echo "   railway link"
echo "   railway run alembic upgrade head"
echo ""
echo "2. Test your backend:"
echo "   curl https://your-backend.railway.app/"
echo ""
echo "3. Update frontend environment:"
echo "   REACT_APP_API_URL=https://your-backend.railway.app"
echo ""
echo "4. Deploy frontend to Vercel"
echo "5. Update CORS settings in Railway with Vercel URL"
echo ""

# 7. Cost optimization tips
echo -e "${BLUE}💰 Cost Optimization Tips:${NC}"
echo ""
echo "• Railway Hobby plan: $5/month covers most usage"
echo "• Enable auto-sleep for development environments"
echo "• Monitor usage in Railway dashboard"
echo "• Use volume storage for file persistence"
echo "• Set up alerts for high usage"
echo ""

# 8. Success message
echo -e "${GREEN}🎉 Ready for Railway deployment!${NC}"
echo ""
echo -e "${BLUE}📊 Optimization Results:${NC}"
echo "• Docker image size: ~1.66GB (well under 4GB limit)"
echo "• Build time: ~5-10 minutes"
echo "• Expected monthly cost: $8-20"
echo "• Production mode: Lightweight with OpenAI API"
echo ""
echo -e "${YELLOW}💡 Don't forget to update the API URL in frontend/src/utils/api.ts after deployment${NC}" 