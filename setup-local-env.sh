#!/bin/bash

# Setup Local Development Environment
echo "🚀 Setting up local development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate secure secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 This script will help you set up local environment files.${NC}"
echo -e "${YELLOW}Your production deployment configs will remain separate.${NC}"
echo ""

# Generate secret key
echo -e "${GREEN}🔑 Generating secure secret key...${NC}"
SECRET_KEY=$(generate_secret_key)

# Setup backend .env
echo -e "${GREEN}⚙️  Setting up backend environment file...${NC}"

if [ ! -f "backend/.env" ]; then
    cat > backend/.env << EOF
# Local Development Environment Configuration
# DO NOT use these values in production!

# Database Configuration (local)
DATABASE_URL=postgresql://postgres:password@localhost:5432/meeting_transcription_dev

# Security Configuration
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (you need to add your actual keys)
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-google-gemini-api-key-here

# Email Configuration (for local testing - use real SMTP for production)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Local Development Settings
ENVIRONMENT=development
STORAGE_PATH=storage
BACKEND_CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1

# Features
SHOW_BACKEND_LOGS=true
AUTO_CLEANUP_AUDIO_FILES=false
EOF

    echo -e "${GREEN}✅ Created backend/.env${NC}"
    echo -e "${YELLOW}⚠️  Please update the API keys in backend/.env${NC}"
else
    echo -e "${YELLOW}⚠️  backend/.env already exists, skipping...${NC}"
fi

# Setup frontend .env.local
echo -e "${GREEN}⚙️  Setting up frontend environment file...${NC}"

if [ ! -f "frontend/.env.local" ]; then
    cat > frontend/.env.local << EOF
# Local Development Environment Configuration
REACT_APP_API_URL=http://localhost:8000
EOF

    echo -e "${GREEN}✅ Created frontend/.env.local${NC}"
else
    echo -e "${YELLOW}⚠️  frontend/.env.local already exists, skipping...${NC}"
fi

# Create .gitignore entries (in case they're missing)
echo -e "${GREEN}🔒 Ensuring .env files are in .gitignore...${NC}"

# Backend .gitignore
if ! grep -q "^\.env$" backend/.gitignore 2>/dev/null; then
    echo ".env" >> backend/.gitignore
    echo -e "${GREEN}✅ Added .env to backend/.gitignore${NC}"
fi

# Frontend .gitignore
if ! grep -q "^\.env\.local$" frontend/.gitignore 2>/dev/null; then
    echo ".env.local" >> frontend/.gitignore
    echo -e "${GREEN}✅ Added .env.local to frontend/.gitignore${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}🎉 Local development environment setup complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Update backend/.env with your actual API keys:"
echo "   - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)"
echo "   - GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)"
echo "   - Email SMTP credentials for password reset functionality"
echo ""
echo "2. Set up local PostgreSQL database:"
echo "   - Install PostgreSQL locally"
echo "   - Create database: createdb meeting_transcription_dev"
echo "   - Or update DATABASE_URL to use SQLite for simple testing"
echo ""
echo "3. Install dependencies:"
echo "   - Backend: cd backend && pip install -r requirements.txt"
echo "   - Frontend: cd frontend && npm install"
echo ""
echo "4. Run database migrations:"
echo "   - cd backend && alembic upgrade head"
echo ""
echo "5. Start development servers:"
echo "   - Backend: cd backend && python main.py"
echo "   - Frontend: cd frontend && npm start"
echo ""
echo -e "${GREEN}🚀 Happy coding!${NC}" 