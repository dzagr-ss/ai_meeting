#!/bin/bash

# Test deployment script for Railway backend and Vercel frontend

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="https://aimeeting.up.railway.app"
FRONTEND_URL="https://ai-meeting-indol.vercel.app"

echo -e "${BLUE}🚀 Testing Deployment Configuration${NC}"
echo "=================================="

# Test 1: Backend Health Check
echo -e "\n${YELLOW}1. Testing Backend Health...${NC}"
if curl -s "$BACKEND_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
fi

# Test 2: CORS Preflight Request
echo -e "\n${YELLOW}2. Testing CORS Configuration...${NC}"
CORS_RESPONSE=$(curl -s -I -X OPTIONS \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    "$BACKEND_URL/users/")

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ CORS headers are present${NC}"
    echo "$CORS_RESPONSE" | grep "Access-Control-Allow-Origin"
else
    echo -e "${RED}✗ CORS headers are missing${NC}"
fi

# Test 3: Frontend Accessibility
echo -e "\n${YELLOW}3. Testing Frontend...${NC}"
if curl -s "$FRONTEND_URL" > /dev/null; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend is not accessible${NC}"
fi

# Test 4: API Endpoint Test
echo -e "\n${YELLOW}4. Testing API Endpoint...${NC}"
API_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/")
if [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API root endpoint is working${NC}"
else
    echo -e "${RED}✗ API root endpoint returned: $API_RESPONSE${NC}"
fi

echo -e "\n${BLUE}📋 Manual Steps Required:${NC}"
echo "=================================="
echo "1. Go to Railway Dashboard: https://railway.app/dashboard"
echo "2. Select your backend service"
echo "3. Go to Variables tab"
echo "4. Add/Update: BACKEND_CORS_ORIGINS = https://ai-meeting-indol.vercel.app,http://localhost:3000"
echo "5. Redeploy the service"
echo ""
echo -e "${YELLOW}Expected CORS Origins:${NC}"
echo "- https://ai-meeting-indol.vercel.app (your Vercel frontend)"
echo "- http://localhost:3000 (for local development)"
echo ""
echo -e "${BLUE}After setting the environment variable, test again with:${NC}"
echo "curl -I -X OPTIONS -H \"Origin: $FRONTEND_URL\" $BACKEND_URL/users/" 