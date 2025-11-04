#!/bin/bash

# Script de testing para Admin Service
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

GATEWAY_URL="http://localhost:8080"
AUTH_URL="http://localhost:5001"

echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  HeartGuard Admin Service - Suite de Pruebas         ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que los servicios estén corriendo
echo -e "${BLUE}Verificando servicios...${NC}"
if ! curl -s http://localhost:5001/health > /dev/null; then
    echo -e "${RED}✗ Auth Service no está corriendo en puerto 5001${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Auth Service corriendo${NC}"

if ! curl -s http://localhost:5002/health > /dev/null; then
    echo -e "${RED}✗ Admin Service no está corriendo en puerto 5002${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Admin Service corriendo${NC}"

if ! curl -s http://localhost:8080/health > /dev/null; then
    echo -e "${RED}✗ Gateway no está corriendo en puerto 8080${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Gateway corriendo${NC}"
echo ""

# Login
echo -e "${BLUE}1.1: POST /auth/login/user - Login org_admin${NC}"
ADMIN_EMAIL="ana.ruiz@heartguard.com"
ADMIN_PASSWORD="Demo#2025"

ADMIN_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$AUTH_URL/auth/login/user" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")

HTTP_CODE=$(echo "$ADMIN_LOGIN" | tail -n1)
RESPONSE_BODY=$(echo "$ADMIN_LOGIN" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Login exitoso${NC}"
    ADMIN_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "  Token: ${ADMIN_TOKEN:0:30}..."
else
    echo -e "${RED}✗ Login falló (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Listar organizaciones
echo -e "${BLUE}2.1: GET /admin/organizations/ - Listar organizaciones${NC}"
LIST_ORGS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_ORGS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_ORGS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Organizaciones listadas (XML)${NC}"
    ORG_ID=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<id>)[^<]+' | head -1)
    ORG_NAME=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<name>)[^<]+' | head -1)
    echo "  Organización: $ORG_NAME (ID: $ORG_ID)"
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Dashboard
echo -e "${BLUE}2.2: GET /admin/organizations/$ORG_ID/dashboard - Dashboard${NC}"
DASHBOARD=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$DASHBOARD" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Dashboard obtenido (XML)${NC}"
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Listar pacientes
echo -e "${BLUE}2.3: GET /admin/organizations/$ORG_ID/patients/ - Listar pacientes${NC}"
LIST_PATIENTS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/patients/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_PATIENTS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_PATIENTS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Pacientes listados (XML)${NC}"
    PATIENT_ID=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<id>)[^<]+' | head -1)
    echo "  Primer Patient ID: $PATIENT_ID"
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Listar alertas
echo -e "${BLUE}2.4: GET /admin/organizations/$ORG_ID/alerts/ - Listar alertas${NC}"
LIST_ALERTS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/alerts/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_ALERTS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_ALERTS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Alertas listadas (XML)${NC}"
    ALERT_ID=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<id>)[^<]+' | head -1)
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Listar dispositivos
echo -e "${BLUE}2.5: GET /admin/organizations/$ORG_ID/devices/ - Listar dispositivos${NC}"
LIST_DEVICES=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/devices/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_DEVICES" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Dispositivos listados (XML)${NC}"
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Listar push devices  
echo -e "${BLUE}2.6: GET /admin/organizations/$ORG_ID/push-devices/ - Listar push devices${NC}"
LIST_PUSH=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/push-devices/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_PUSH" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Push devices listados (XML)${NC}"
else
    echo -e "${RED}✗ Error (HTTP $HTTP_CODE)${NC}"
fi
echo ""

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Suite de pruebas completada exitosamente${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
