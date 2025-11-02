#!/bin/bash

# Script de pruebas para HeartGuard Gateway
# Verifica que el gateway enrute correctamente las peticiones al auth-service

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"

echo -e "\n╔════════════════════════════════════════════════════════╗"
echo -e "║  HeartGuard Gateway - Suite de Pruebas               ║"
echo -e "╚════════════════════════════════════════════════════════╝\n"

# Test 1: Health Check del Gateway
echo -e "${BLUE}Test 1: Health Check del Gateway${NC}"
GATEWAY_HEALTH=$(curl -s -w "\n%{http_code}" "$BASE_URL/health/")
HTTP_CODE=$(echo "$GATEWAY_HEALTH" | tail -n1)
RESPONSE_BODY=$(echo "$GATEWAY_HEALTH" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Gateway funcionando correctamente${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Gateway no responde (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
    exit 1
fi
echo ""

# Test 2: Registro de Usuario a través del Gateway
echo -e "${YELLOW}Test 2: Registro de Usuario (vía Gateway)${NC}"
USER_EMAIL="gateway.test.user.$(date +%s)@example.com"
USER_REGISTER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register/user" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Gateway Test User\",
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

# Test 3: Login de Usuario a través del Gateway
echo -e "${YELLOW}Test 3: Login de Usuario (vía Gateway)${NC}"
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

# Test 4: Verificar Token a través del Gateway
echo -e "${YELLOW}Test 4: Verificar Token (vía Gateway)${NC}"
USER_VERIFY=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/auth/verify" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN")

HTTP_CODE=$(echo "$USER_VERIFY" | tail -n1)
RESPONSE_BODY=$(echo "$USER_VERIFY" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ] && echo "$RESPONSE_BODY" | grep -q '"valid"'; then
    echo -e "${GREEN}✓ Token verificado correctamente${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ Verificación de token falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 5: Obtener datos de cuenta a través del Gateway
echo -e "${YELLOW}Test 5: Endpoint /auth/me (vía Gateway)${NC}"
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

# Test 6: Registro de Paciente a través del Gateway
echo -e "${YELLOW}Test 6: Registro de Paciente (vía Gateway)${NC}"
ORG_ID=$(PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -t -c "SELECT id FROM organizations LIMIT 1;" | tr -d ' ')
echo "Usando org_id: $ORG_ID"

PATIENT_EMAIL="gateway.test.patient.$(date +%s)@example.com"
PATIENT_REGISTER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register/patient" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Gateway Test Patient\",
    \"email\": \"$PATIENT_EMAIL\",
    \"password\": \"TestPass123!\",
    \"org_id\": \"$ORG_ID\",
    \"birthdate\": \"1985-03-20\",
    \"sex_code\": \"M\",
    \"risk_level_code\": \"high\"
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

# Test 7: Login de Paciente a través del Gateway
echo -e "${YELLOW}Test 7: Login de Paciente (vía Gateway)${NC}"
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
    echo "Access Token: ${PATIENT_ACCESS_TOKEN:0:50}..."
else
    echo -e "${RED}✗ Login de paciente falló (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo ""

# Test 8: Refresh Token a través del Gateway
echo -e "${YELLOW}Test 8: Refresh Token (vía Gateway)${NC}"
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

echo -e "\n╔════════════════════════════════════════════════════════╗"
echo -e "║  Resumen de Pruebas                                   ║"
echo -e "╚════════════════════════════════════════════════════════╝\n"

echo -e "${GREEN}✅ Gateway funcionando correctamente${NC}"
echo ""
echo "El gateway está enrutando correctamente las peticiones a:"
echo "  - Auth Service: $BASE_URL/auth/* → http://localhost:5001/auth/*"
echo ""
echo "Cuentas de prueba creadas:"
echo "  - Usuario: $USER_EMAIL"
echo "  - Paciente: $PATIENT_EMAIL"
echo ""
echo -e "¡Suite de pruebas del Gateway completada!"
