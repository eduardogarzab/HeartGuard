#!/bin/bash
# Test script for Media Service through Gateway

set -e

echo "=========================================="
echo "  Media Service Integration Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
GATEWAY_URL="http://localhost:8080"
USER_ID="11111111-1111-1111-1111-111111111111"
PATIENT_ID="22222222-2222-2222-2222-222222222222"
TEST_IMAGE="/home/azureuser/HeartGuard/jorge.jpg"

# Generate fresh tokens
echo "Generating test tokens..."
cd "$(dirname "$0")"
TOKEN_OUTPUT=$(python3 generate_test_token.py)
USER_TOKEN=$(echo "$TOKEN_OUTPUT" | grep -A 1 "User Token:" | tail -1 | tr -d ' ')
PATIENT_TOKEN=$(echo "$TOKEN_OUTPUT" | grep -A 1 "Patient Token:" | tail -1 | tr -d ' ')

echo "✓ Tokens generated"
echo ""

# Test 1: Health check
echo "Test 1: Health check through gateway"
RESPONSE=$(curl -s "$GATEWAY_URL/media/health")
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ PASS${NC} - Health check successful"
else
    echo -e "${RED}✗ FAIL${NC} - Health check failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 2: Upload user photo (JSON response)
echo "Test 2: Upload user photo (JSON)"
RESPONSE=$(curl -s -X POST "$GATEWAY_URL/media/users/$USER_ID/photo" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -F "photo=@$TEST_IMAGE")
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    PHOTO_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['photo']['url'])")
    echo -e "${GREEN}✓ PASS${NC} - Photo uploaded successfully"
    echo "  URL: $PHOTO_URL"
else
    echo -e "${RED}✗ FAIL${NC} - Upload failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 3: Upload user photo (XML response)
echo "Test 3: Upload user photo (XML)"
RESPONSE=$(curl -s -X POST "$GATEWAY_URL/media/users/$USER_ID/photo" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Accept: application/xml" \
    -F "photo=@$TEST_IMAGE")
if echo "$RESPONSE" | grep -q '<status>success</status>'; then
    echo -e "${GREEN}✓ PASS${NC} - Photo uploaded with XML response"
else
    echo -e "${RED}✗ FAIL${NC} - XML upload failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 4: Delete user photo
echo "Test 4: Delete user photo"
RESPONSE=$(curl -s -X DELETE "$GATEWAY_URL/media/users/$USER_ID/photo" \
    -H "Authorization: Bearer $USER_TOKEN")
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ PASS${NC} - Photo deleted successfully"
else
    echo -e "${RED}✗ FAIL${NC} - Delete failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 5: Upload patient photo
echo "Test 5: Upload patient photo"
RESPONSE=$(curl -s -X POST "$GATEWAY_URL/media/patients/$PATIENT_ID/photo" \
    -H "Authorization: Bearer $PATIENT_TOKEN" \
    -F "photo=@$TEST_IMAGE")
if echo "$RESPONSE" | grep -q '"status":"success"'; then
    PHOTO_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['photo']['url'])")
    echo -e "${GREEN}✓ PASS${NC} - Patient photo uploaded"
    echo "  URL: $PHOTO_URL"
else
    echo -e "${RED}✗ FAIL${NC} - Patient upload failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 6: Authorization - patient trying to delete another patient's photo
echo "Test 6: Authorization check (should fail)"
FAKE_PATIENT_ID="33333333-3333-3333-3333-333333333333"
RESPONSE=$(curl -s -X DELETE "$GATEWAY_URL/media/patients/$FAKE_PATIENT_ID/photo" \
    -H "Authorization: Bearer $PATIENT_TOKEN")
if echo "$RESPONSE" | grep -q '"status":"fail"' && echo "$RESPONSE" | grep -q 'forbidden'; then
    echo -e "${GREEN}✓ PASS${NC} - Authorization properly enforced"
else
    echo -e "${RED}✗ FAIL${NC} - Authorization check failed"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 7: No token (should fail)
echo "Test 7: Request without token (should fail)"
RESPONSE=$(curl -s -X POST "$GATEWAY_URL/media/users/$USER_ID/photo" \
    -F "photo=@$TEST_IMAGE")
if echo "$RESPONSE" | grep -q 'unauthorized'; then
    echo -e "${GREEN}✓ PASS${NC} - Properly rejected request without token"
else
    echo -e "${RED}✗ FAIL${NC} - Should have rejected request"
    echo "$RESPONSE"
    exit 1
fi
echo ""

# Test 8: Verify photo is accessible via CDN
echo "Test 8: Verify CDN accessibility"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PHOTO_URL")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Photo is publicly accessible via CDN"
else
    echo -e "${RED}✗ FAIL${NC} - Photo not accessible (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# Cleanup
echo "Cleanup: Deleting test patient photo"
curl -s -X DELETE "$GATEWAY_URL/media/patients/$PATIENT_ID/photo" \
    -H "Authorization: Bearer $PATIENT_TOKEN" > /dev/null

echo ""
echo "=========================================="
echo -e "${GREEN}  ✓ ALL TESTS PASSED${NC}"
echo "=========================================="
