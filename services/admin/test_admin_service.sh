#!/bin/bash

# Script de testing para Admin Service
# Requiere que todos los servicios estén ejecutándose
# Ejecuta primero: ./start_services.sh

# Colores
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
if ! curl -s http://localhost:5001/health/ > /dev/null; then
    echo -e "${RED}✗ Auth Service no está corriendo en puerto 5001${NC}"
    echo -e "${YELLOW}Ejecuta primero: ./start_services.sh${NC}"
    exit 1
fi

if ! curl -s http://localhost:5002/health/ > /dev/null; then
    echo -e "${RED}✗ Admin Service no está corriendo en puerto 5002${NC}"
    echo -e "${YELLOW}Ejecuta primero: ./start_services.sh${NC}"
    exit 1
fi

if ! curl -s http://localhost:8080/health/ > /dev/null; then
    echo -e "${RED}✗ Gateway no está corriendo en puerto 8080${NC}"
    echo -e "${YELLOW}Ejecuta primero: ./start_services.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Todos los servicios están activos${NC}"
echo ""

# =============================================================================
# FASE 1: PREPARACIÓN - Crear usuarios y organización
# =============================================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 1: Preparación - Crear usuarios de prueba${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

# 1.1: Usar usuario existente de seed (ana.ruiz@heartguard.com)
echo -e "${BLUE}1.1: Usando usuario existente de seed${NC}"
ADMIN_EMAIL="ana.ruiz@heartguard.com"
ADMIN_PASSWORD="Demo#2025"

# Obtener el user_id
ADMIN_USER_ID=$(PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -t -c "SELECT id FROM users WHERE email='$ADMIN_EMAIL';" 2>/dev/null | tr -d ' ')

if [ -z "$ADMIN_USER_ID" ]; then
    echo -e "${RED}✗ Usuario $ADMIN_EMAIL no encontrado en BD${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Usuario encontrado${NC}"
echo "  Email: $ADMIN_EMAIL"
echo "  User ID: $ADMIN_USER_ID"
echo ""

# 1.2: Obtener organización del usuario (FAM-001)
echo -e "${BLUE}1.2: Obtener organización del usuario${NC}"
ORG_ID=$(PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -t -c "
    SELECT org_id FROM user_org_membership 
    WHERE user_id='$ADMIN_USER_ID' 
    LIMIT 1;" 2>/dev/null | tr -d ' ')

if [ -z "$ORG_ID" ]; then
    echo -e "${RED}✗ Usuario no tiene membresía en ninguna organización${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Organización: $ORG_ID${NC}"
echo ""

# 1.3: Login del admin
echo -e "${BLUE}1.3: Login del usuario admin${NC}"
ADMIN_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$AUTH_URL/auth/login/user" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$ADMIN_EMAIL\",
    \"password\": \"$ADMIN_PASSWORD\"
  }")

HTTP_CODE=$(echo "$ADMIN_LOGIN" | tail -n1)
RESPONSE_BODY=$(echo "$ADMIN_LOGIN" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Login exitoso${NC}"
    ADMIN_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "  Token: ${ADMIN_TOKEN:0:50}..."
else
    echo -e "${RED}✗ Error en login (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | python3 -m json.tool
    exit 1
fi
echo ""

# =============================================================================
# FASE 2: PRUEBAS DE ADMIN SERVICE VIA GATEWAY
# =============================================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 2: Pruebas de Admin Service (via Gateway)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

# 2.1: Listar organizaciones
echo -e "${BLUE}2.1: GET /admin/organizations/ - Listar organizaciones${NC}"
LIST_ORGS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_ORGS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_ORGS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Organizaciones listadas (XML)${NC}"
    echo "$RESPONSE_BODY" | head -10
else
    echo -e "${RED}✗ Error al listar organizaciones (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.2: Obtener detalle de organización
echo -e "${BLUE}2.2: GET /admin/organizations/$ORG_ID - Detalle de organización${NC}"
GET_ORG=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$GET_ORG" | tail -n1)
RESPONSE_BODY=$(echo "$GET_ORG" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Detalle de organización obtenido (XML)${NC}"
    echo "$RESPONSE_BODY" | head -15
else
    echo -e "${RED}✗ Error al obtener organización (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.3: Dashboard de organización
echo -e "${BLUE}2.3: GET /admin/organizations/$ORG_ID/dashboard - Dashboard${NC}"
GET_DASHBOARD=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/dashboard" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$GET_DASHBOARD" | tail -n1)
RESPONSE_BODY=$(echo "$GET_DASHBOARD" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Dashboard obtenido (XML)${NC}"
    echo "$RESPONSE_BODY" | head -20
else
    echo -e "${RED}✗ Error al obtener dashboard (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.4: Crear paciente via Admin Service
echo -e "${BLUE}2.4: POST /admin/organizations/$ORG_ID/patients/ - Crear paciente${NC}"
PATIENT_EMAIL="patient.admin.$(date +%s)@example.com"
CREATE_PATIENT=$(curl -s -w "\n%{http_code}" -X POST "$GATEWAY_URL/admin/organizations/$ORG_ID/patients/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Paciente Test Admin\",
    \"email\": \"$PATIENT_EMAIL\",
    \"password\": \"PatientPass123!\",
    \"birthdate\": \"1985-03-20\",
    \"sex_code\": \"M\",
    \"risk_level_code\": \"high\"
  }")

HTTP_CODE=$(echo "$CREATE_PATIENT" | tail -n1)
RESPONSE_BODY=$(echo "$CREATE_PATIENT" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✓ Paciente creado (XML)${NC}"
    # Parsear XML para obtener patient_id
    PATIENT_ID=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<id>)[^<]+' | head -1)
    echo "  Patient ID: $PATIENT_ID"
    echo "  Email: $PATIENT_EMAIL"
    echo "$RESPONSE_BODY" | head -15
else
    echo -e "${RED}✗ Error al crear paciente (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.5: Listar pacientes
echo -e "${BLUE}2.5: GET /admin/organizations/$ORG_ID/patients/ - Listar pacientes${NC}"
LIST_PATIENTS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/patients/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_PATIENTS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_PATIENTS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Pacientes listados (XML)${NC}"
    PATIENT_COUNT=$(echo "$RESPONSE_BODY" | grep -c '<patient>' || echo "0")
    echo "  Total de pacientes: $PATIENT_COUNT"
    echo "$RESPONSE_BODY" | head -20
else
    echo -e "${RED}✗ Error al listar pacientes (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.6: Obtener detalle de paciente
if [ ! -z "$PATIENT_ID" ]; then
    echo -e "${BLUE}2.6: GET /admin/organizations/$ORG_ID/patients/$PATIENT_ID - Detalle paciente${NC}"
    GET_PATIENT=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/patients/$PATIENT_ID" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Accept: application/xml")

    HTTP_CODE=$(echo "$GET_PATIENT" | tail -n1)
    RESPONSE_BODY=$(echo "$GET_PATIENT" | sed '$d')

    if [ "$HTTP_CODE" -eq 200 ]; then
        echo -e "${GREEN}✓ Detalle de paciente obtenido (XML)${NC}"
        echo "$RESPONSE_BODY" | head -20
    else
        echo -e "${RED}✗ Error al obtener paciente (HTTP $HTTP_CODE)${NC}"
        echo "$RESPONSE_BODY"
    fi
    echo ""
fi

# 2.7: Crear Care Team
echo -e "${BLUE}2.7: POST /admin/organizations/$ORG_ID/care-teams/ - Crear equipo${NC}"
CREATE_TEAM=$(curl -s -w "\n%{http_code}" -X POST "$GATEWAY_URL/admin/organizations/$ORG_ID/care-teams/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Equipo Cardiología Test\",
    \"description\": \"Equipo de prueba para tests\"
  }")

HTTP_CODE=$(echo "$CREATE_TEAM" | tail -n1)
RESPONSE_BODY=$(echo "$CREATE_TEAM" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✓ Care team creado (XML)${NC}"
    TEAM_ID=$(echo "$RESPONSE_BODY" | grep -oP '(?<=<id>)[^<]+' | head -1)
    echo "  Team ID: $TEAM_ID"
    echo "$RESPONSE_BODY" | head -15
else
    echo -e "${RED}✗ Error al crear care team (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.8: Listar Care Teams
echo -e "${BLUE}2.8: GET /admin/organizations/$ORG_ID/care-teams/ - Listar equipos${NC}"
LIST_TEAMS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/care-teams/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_TEAMS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_TEAMS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Care teams listados (XML)${NC}"
    echo "$RESPONSE_BODY" | head -20
else
    echo -e "${RED}✗ Error al listar care teams (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.9: Listar tipos de relación de caregivers
echo -e "${BLUE}2.9: GET /admin/organizations/$ORG_ID/caregivers/relationship-types${NC}"
LIST_REL_TYPES=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/caregivers/relationship-types" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_REL_TYPES" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_REL_TYPES" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Tipos de relación listados (XML)${NC}"
    echo "$RESPONSE_BODY" | head -20
else
    echo -e "${RED}✗ Error al listar tipos de relación (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# 2.10: Listar alertas
echo -e "${BLUE}2.10: GET /admin/organizations/$ORG_ID/alerts/ - Listar alertas${NC}"
LIST_ALERTS=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/$ORG_ID/alerts/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$LIST_ALERTS" | tail -n1)
RESPONSE_BODY=$(echo "$LIST_ALERTS" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Alertas listadas (XML)${NC}"
    ALERT_COUNT=$(echo "$RESPONSE_BODY" | grep -c '<alert>' || echo "0")
    echo "  Total de alertas: $ALERT_COUNT"
    echo "$RESPONSE_BODY" | head -20
else
    echo -e "${RED}✗ Error al listar alertas (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY"
fi
echo ""

# =============================================================================
# FASE 3: PRUEBAS DE AUTORIZACIÓN
# =============================================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  FASE 3: Pruebas de Autorización${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""

# 3.1: Intentar acceso sin token
echo -e "${BLUE}3.1: Acceso sin token (debe fallar)${NC}"
NO_TOKEN=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/" \
  -H "Accept: application/xml")

HTTP_CODE=$(echo "$NO_TOKEN" | tail -n1)

if [ "$HTTP_CODE" -eq 401 ]; then
    echo -e "${GREEN}✓ Acceso denegado correctamente (HTTP 401)${NC}"
else
    echo -e "${RED}✗ Debería rechazar sin token (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# 3.2: Usar usuario sin permisos org_admin (Carlos Vega)
echo -e "${BLUE}3.2: Usando usuario sin rol org_admin${NC}"
NORMAL_EMAIL="carlos.vega@heartguard.com"
NORMAL_PASSWORD="Demo#2025"

# Login del usuario sin permisos
NORMAL_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$AUTH_URL/auth/login/user" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$NORMAL_EMAIL\", \"password\": \"$NORMAL_PASSWORD\"}")

HTTP_CODE=$(echo "$NORMAL_LOGIN" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Usuario sin permisos logueado${NC}"
    NORMAL_TOKEN=$(echo "$NORMAL_LOGIN" | sed '$d' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    
    # Intentar acceder a admin endpoint
    echo -e "${BLUE}3.3: Intentar acceso sin permisos org_admin (debe fallar)${NC}"
    UNAUTHORIZED=$(curl -s -w "\n%{http_code}" -X GET "$GATEWAY_URL/admin/organizations/" \
      -H "Authorization: Bearer $NORMAL_TOKEN" \
      -H "Accept: application/xml")
    
    HTTP_CODE=$(echo "$UNAUTHORIZED" | tail -n1)
    if [ "$HTTP_CODE" -eq 403 ]; then
        echo -e "${GREEN}✓ Acceso denegado correctamente (HTTP 403 - Forbidden)${NC}"
    else
        echo -e "${RED}✗ Debería rechazar usuario sin permisos (HTTP $HTTP_CODE)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No se pudo loguear usuario sin permisos (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# =============================================================================
# RESUMEN
# =============================================================================

echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Resumen de Pruebas Completadas                       ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Datos de prueba creados:${NC}"
echo "  - Organización: $ORG_ID"
echo "  - Admin User: $ADMIN_EMAIL"
echo "  - Admin Token: ${ADMIN_TOKEN:0:30}..."
if [ ! -z "$PATIENT_ID" ]; then
    echo "  - Paciente: $PATIENT_EMAIL (ID: $PATIENT_ID)"
fi
if [ ! -z "$TEAM_ID" ]; then
    echo "  - Care Team: $TEAM_ID"
fi
echo ""
echo -e "${GREEN}Endpoints probados:${NC}"
echo "  ✓ Listar organizaciones"
echo "  ✓ Detalle de organización"
echo "  ✓ Dashboard"
echo "  ✓ Crear paciente (XML)"
echo "  ✓ Listar pacientes"
echo "  ✓ Detalle de paciente"
echo "  ✓ Crear care team"
echo "  ✓ Listar care teams"
echo "  ✓ Tipos de relación caregivers"
echo "  ✓ Listar alertas"
echo "  ✓ Validación de autorización"
echo ""
echo -e "${YELLOW}¡Suite de pruebas del Admin Service completada!${NC}"
