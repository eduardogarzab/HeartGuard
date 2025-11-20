#!/bin/bash

# Script de testing para Auth Service
# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:5001"

echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  HeartGuard Auth Service - Suite de Pruebas          ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Health Check
echo -e "\n${BLUE}Test 1: Health Check${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:5001/health/)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check exitoso${NC}"
    echo "$RESPONSE_BODY" | jq .
else
    echo -e "${RED}✗ Health check falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# Test 2: Registro de Usuario
echo -e "${YELLOW}Test 2: Registro de Usuario (Staff)${NC}"
USER_EMAIL="test.user.$(date +%s)@example.com"
USER_REGISTER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register/user" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Dr. Test Usuario\",
    \"email\": \"$USER_EMAIL\",
    \"password\": \"TestPass123!\"
  }")

HTTP_CODE=$(echo "$USER_REGISTER" | tail -n1)
RESPONSE_BODY=$(echo "$USER_REGISTER" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✓ Registro de usuario exitoso${NC}"
    USER_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['user_id'])")
    echo "User ID: $USER_ID"
    echo "Email: $USER_EMAIL"
else
    echo -e "${RED}✗ Registro de usuario falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 3: Login de Usuario
echo -e "${YELLOW}Test 3: Login de Usuario${NC}"
USER_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login/user" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$USER_EMAIL\",
    \"password\": \"TestPass123!\"
  }")

HTTP_CODE=$(echo "$USER_LOGIN" | tail -n1)
RESPONSE_BODY=$(echo "$USER_LOGIN" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Login de usuario exitoso${NC}"
    USER_ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    USER_REFRESH_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")
    echo "Access Token: ${USER_ACCESS_TOKEN:0:50}..."
    echo "Refresh Token: ${USER_REFRESH_TOKEN:0:50}..."
else
    echo -e "${RED}✗ Login de usuario falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 4: Verificar Token de Usuario
echo -e "${YELLOW}Test 4: Verificar Token de Usuario${NC}"
USER_VERIFY=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/auth/verify" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN")

HTTP_CODE=$(echo "$USER_VERIFY" | tail -n1)
RESPONSE_BODY=$(echo "$USER_VERIFY" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] && echo "$RESPONSE_BODY" | grep -q '"valid"'; then
    echo -e "${GREEN}✓ Token válido${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Token inválido (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 5: Endpoint /auth/me para Usuario
echo -e "${YELLOW}Test 5: Endpoint /auth/me para Usuario${NC}"
USER_ME=$(curl -s -w "\n%{http_code}" "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN")

HTTP_CODE=$(echo "$USER_ME" | tail -n1)
RESPONSE_BODY=$(echo "$USER_ME" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] && echo "$RESPONSE_BODY" | grep -q '"account_type"'; then
    echo -e "${GREEN}✓ Datos de usuario obtenidos correctamente${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Error obteniendo datos de usuario (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 6: Obtener org_id para paciente
echo -e "${YELLOW}Test 6: Registro de Paciente${NC}"
ORG_ID=$(PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -t -c "SELECT id FROM organizations LIMIT 1;" | tr -d ' ')
echo "Usando org_id: $ORG_ID"

PATIENT_EMAIL="test.patient.$(date +%s)@example.com"
PATIENT_REGISTER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register/patient" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"María Test Paciente\",
    \"email\": \"$PATIENT_EMAIL\",
    \"password\": \"TestPass123!\",
    \"org_id\": \"$ORG_ID\",
    \"birthdate\": \"1990-05-15\",
    \"sex_code\": \"F\",
    \"risk_level_code\": \"medium\"
  }")

HTTP_CODE=$(echo "$PATIENT_REGISTER" | tail -n1)
RESPONSE_BODY=$(echo "$PATIENT_REGISTER" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✓ Registro de paciente exitoso${NC}"
    PATIENT_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['patient_id'])")
    echo "Patient ID: $PATIENT_ID"
    echo "Email: $PATIENT_EMAIL"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Registro de paciente falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 7: Login de Paciente
echo -e "${YELLOW}Test 7: Login de Paciente${NC}"
PATIENT_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login/patient" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$PATIENT_EMAIL\",
    \"password\": \"TestPass123!\"
  }")

HTTP_CODE=$(echo "$PATIENT_LOGIN" | tail -n1)
RESPONSE_BODY=$(echo "$PATIENT_LOGIN" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Login de paciente exitoso${NC}"
    PATIENT_ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    PATIENT_REFRESH_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")
    echo "Access Token: ${PATIENT_ACCESS_TOKEN:0:50}..."
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -15
else
    echo -e "${RED}✗ Login de paciente falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 8: Verificar Token de Paciente
echo -e "${YELLOW}Test 8: Verificar Token de Paciente${NC}"
PATIENT_VERIFY=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/auth/verify" \
  -H "Authorization: Bearer $PATIENT_ACCESS_TOKEN")

HTTP_CODE=$(echo "$PATIENT_VERIFY" | tail -n1)
RESPONSE_BODY=$(echo "$PATIENT_VERIFY" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] && echo "$RESPONSE_BODY" | grep -q '"valid"'; then
    echo -e "${GREEN}✓ Token de paciente válido${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Token de paciente inválido (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 9: Endpoint /auth/me para Paciente
echo -e "${YELLOW}Test 9: Endpoint /auth/me para Paciente${NC}"
PATIENT_ME=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $PATIENT_ACCESS_TOKEN")

HTTP_CODE=$(echo "$PATIENT_ME" | tail -n1)
RESPONSE_BODY=$(echo "$PATIENT_ME" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] && echo "$RESPONSE_BODY" | grep -q '"account_type"'; then
    echo -e "${GREEN}✓ /auth/me para paciente exitoso${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ /auth/me para paciente falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 10: Refresh Token para Usuario
echo -e "${YELLOW}Test 10: Refresh Token para Usuario${NC}"
USER_REFRESH=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$USER_REFRESH_TOKEN\"
  }")

HTTP_CODE=$(echo "$USER_REFRESH" | tail -n1)
RESPONSE_BODY=$(echo "$USER_REFRESH" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Refresh token exitoso${NC}"
    NEW_ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "Nuevo Access Token: ${NEW_ACCESS_TOKEN:0:50}..."
else
    echo -e "${RED}✗ Refresh token falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Resumen
echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Resumen de Pruebas                                   ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Usuarios creados:${NC}"
echo "  - Usuario (staff): $USER_EMAIL (ID: $USER_ID)"
echo "  - Paciente: $PATIENT_EMAIL (ID: $PATIENT_ID)"
echo ""
echo -e "${GREEN}Tokens válidos:${NC}"
echo "  - Usuario Access Token: ${USER_ACCESS_TOKEN:0:30}..."
echo "  - Paciente Access Token: ${PATIENT_ACCESS_TOKEN:0:30}..."
echo ""
echo -e "${YELLOW}¡Suite de pruebas completada!${NC}"
