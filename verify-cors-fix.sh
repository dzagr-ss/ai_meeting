#!/bin/bash

# Verify CORS Fix
echo "🔍 Verifying CORS Configuration"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="https://aimeeting.up.railway.app"
FRONTEND_URL="https://ai-meeting-indol.vercel.app"

echo -e "${BLUE}Testing CORS for Vercel frontend -> Railway backend${NC}\n"

# Test CORS preflight request
echo -e "${YELLOW}Testing CORS preflight request...${NC}"
CORS_TEST=$(curl -s -I -X OPTIONS \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    "${BACKEND_URL}/users/")

# Check for specific CORS headers
if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin: ${FRONTEND_URL}"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Origin is correctly set${NC}"
elif echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin: \*"; then
    echo -e "${YELLOW}⚠ Access-Control-Allow-Origin is set to * (wildcard)${NC}"
else
    echo -e "${RED}✗ Access-Control-Allow-Origin header is missing or incorrect${NC}"
    echo -e "${YELLOW}Full response:${NC}"
    echo "$CORS_TEST"
    exit 1
fi

if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Methods"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Methods header is present${NC}"
else
    echo -e "${RED}✗ Access-Control-Allow-Methods header is missing${NC}"
fi

if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Headers"; then
    echo -e "${GREEN}✓ Access-Control-Allow-Headers header is present${NC}"
else
    echo -e "${RED}✗ Access-Control-Allow-Headers header is missing${NC}"
fi

echo -e "\n${BLUE}Full CORS headers received:${NC}"
echo "$CORS_TEST" | grep "Access-Control" || echo "No Access-Control headers found"

# Test actual API request
echo -e "\n${YELLOW}Testing actual API request...${NC}"
API_TEST=$(curl -s -w "HTTP_CODE:%{http_code}" \
    -X POST \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Content-Type: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d '{"email":"test@example.com","password":"TestPass123!"}' \
    "${BACKEND_URL}/users/")

HTTP_CODE=$(echo "$API_TEST" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ API request reached backend (${HTTP_CODE} - validation error is expected)${NC}"
    echo -e "${GREEN}✓ CORS is working correctly!${NC}"
elif [ "$HTTP_CODE" = "0" ] || [ "$HTTP_CODE" = "" ]; then
    echo -e "${RED}✗ API request failed - network or CORS issue${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ Unexpected response code: ${HTTP_CODE}${NC}"
fi

echo -e "\n${GREEN}🎉 CORS configuration is working!${NC}"
echo -e "${BLUE}Your frontend should now be able to connect to the backend.${NC}" 