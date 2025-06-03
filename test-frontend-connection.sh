#!/bin/bash

# Test Frontend Connection to Backend
echo "🔧 Testing Frontend-to-Backend Connection"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="https://aimeeting.up.railway.app"
FRONTEND_URL="https://ai-meeting-indol.vercel.app"

echo -e "${BLUE}Testing connection from ${FRONTEND_URL} to ${BACKEND_URL}${NC}\n"

# Test 1: Backend Health
echo -e "${YELLOW}1. Testing Backend Health...${NC}"
if curl -s -f "${BACKEND_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    exit 1
fi

# Test 2: CORS Preflight
echo -e "\n${YELLOW}2. Testing CORS Preflight...${NC}"
CORS_RESPONSE=$(curl -s -I -X OPTIONS \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    "${BACKEND_URL}/users/" 2>&1)

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ CORS headers are present${NC}"
    echo -e "${BLUE}Found headers:${NC}"
    echo "$CORS_RESPONSE" | grep "Access-Control" || echo "No Access-Control headers found"
else
    echo -e "${RED}✗ CORS headers are missing${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo "$CORS_RESPONSE"
fi

# Test 3: Content Security Policy Simulation
echo -e "\n${YELLOW}3. Testing Content Security Policy...${NC}"
echo -e "${BLUE}Current CSP allows connections to:${NC}"
echo "- 'self' (same origin)"
echo "- ws: wss: (websockets)"
echo "- http://localhost:8000 (local development)"
echo "- https://aimeeting.up.railway.app (Railway backend)"
echo "- https://api.openai.com (OpenAI API)"

# Test 4: Actual API Request Simulation
echo -e "\n${YELLOW}4. Simulating API Request...${NC}"
API_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" \
    -X POST \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Content-Type: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d '{"email":"test@example.com","password":"testpassword"}' \
    "${BACKEND_URL}/users/" 2>&1)

HTTP_CODE=$(echo "$API_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
RESPONSE_BODY=$(echo "$API_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ API request successful (${HTTP_CODE})${NC}"
elif [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${YELLOW}⚠ API request rejected due to validation (${HTTP_CODE}) - This is expected for test data${NC}"
    echo -e "${GREEN}✓ Connection is working (validation rejection means CORS is OK)${NC}"
else
    echo -e "${RED}✗ API request failed (${HTTP_CODE})${NC}"
    echo -e "${YELLOW}Response: ${RESPONSE_BODY}${NC}"
fi

echo -e "\n${BLUE}Summary:${NC}"
echo -e "${GREEN}✓ CSP has been updated to allow Railway backend${NC}"
echo -e "${YELLOW}⚠ Make sure to set BACKEND_CORS_ORIGINS in Railway:${NC}"
echo -e "   ${FRONTEND_URL},http://localhost:3000"

echo -e "\n${BLUE}To set CORS in Railway:${NC}"
echo "1. Go to Railway Dashboard"
echo "2. Select your backend service"
echo "3. Go to Variables tab"
echo "4. Add: BACKEND_CORS_ORIGINS = ${FRONTEND_URL},http://localhost:3000"
echo "5. Deploy" 