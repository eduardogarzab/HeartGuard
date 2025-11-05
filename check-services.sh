#!/bin/bash

# Script de verificación de servicios HeartGuard
# Verifica que todos los servicios estén corriendo correctamente

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  HeartGuard - Verificación de Servicios              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# Función para verificar servicio HTTP
check_http_service() {
    local name=$1
    local url=$2
    local expected_service=$3

    echo -e "${YELLOW}Verificando $name...${NC}"

    response=$(curl -s -m 5 "$url" 2>&1)
    http_code=$?

    if [ $http_code -eq 0 ]; then
        # Verificar si es XML (admin service)
        if echo "$response" | grep -q '<status>ok</status>'; then
            service_name=$(echo "$response" | grep -o '<service>[^<]*</service>' | sed 's/<[^>]*>//g')
            timestamp=$(echo "$response" | grep -o '<timestamp>[^<]*</timestamp>' | sed 's/<[^>]*>//g')

            echo -e "${GREEN}✓ $name está corriendo${NC}"
            echo -e "  Servicio: $service_name"
            echo -e "  Timestamp: $timestamp"
            return 0
        # Verificar si es JSON (auth, gateway, user)
        elif echo "$response" | grep -q '"status"' && (echo "$response" | grep -q '"ok"' || echo "$response" | grep -q '"success"'); then
            service_name=$(echo "$response" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)
            timestamp=$(echo "$response" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)

            echo -e "${GREEN}✓ $name está corriendo${NC}"
            [ -n "$service_name" ] && echo -e "  Servicio: $service_name"
            [ -n "$timestamp" ] && echo -e "  Timestamp: $timestamp"
            return 0
        else
            echo -e "${RED}✗ $name no responde correctamente${NC}"
            echo -e "  URL: $url"
            return 1
        fi
    else
        echo -e "${RED}✗ $name no responde o está caído${NC}"
        echo -e "  URL: $url"
        return 1
    fi
}

# Función para verificar PostgreSQL
check_postgres() {
    echo -e "${YELLOW}Verificando PostgreSQL...${NC}"

    if docker ps | grep -q postgres; then
        container_status=$(docker ps --format "{{.Status}}" | grep postgres | head -1)
        echo -e "${GREEN}✓ PostgreSQL está corriendo${NC}"
        echo -e "  Estado: $container_status"

        # Intentar conexión
        if PGPASSWORD=dev_change_me psql -h localhost -U heartguard_app -d heartguard -c "SELECT 1;" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Conexión a base de datos exitosa${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ PostgreSQL corriendo pero no se puede conectar${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ PostgreSQL no está corriendo${NC}"
        return 1
    fi
}

# Verificar servicios
gateway_ok=0
auth_ok=0
admin_ok=0
user_ok=0
postgres_ok=0

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

check_http_service "Gateway (Puerto 8080)" "http://localhost:8080/health/" "heartguard-gateway"
gateway_ok=$?

echo ""

check_http_service "Auth Service (Puerto 5001)" "http://localhost:5001/health/" "heartguard-auth"
auth_ok=$?

echo ""

check_http_service "Admin Service (Puerto 5002)" "http://localhost:5002/health/" "heartguard-admin"
admin_ok=$?

echo ""

check_http_service "User Service (Puerto 5003)" "http://localhost:5003/health" "heartguard-user"
user_ok=$?

echo ""

check_postgres
postgres_ok=$?

echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}\n"

# Resumen
echo -e "${BLUE}Resumen de Servicios:${NC}"
echo ""

if [ $gateway_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Gateway         :8080  [Expuesto Públicamente]"
else
    echo -e "${RED}✗${NC} Gateway         :8080  [ERROR]"
fi

if [ $auth_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Auth Service    :5001  [Solo Interno]"
else
    echo -e "${RED}✗${NC} Auth Service    :5001  [ERROR]"
fi

if [ $admin_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Admin Service   :5002  [Solo Interno]"
else
    echo -e "${RED}✗${NC} Admin Service   :5002  [ERROR]"
fi

if [ $user_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} User Service    :5003  [Solo Interno]"
else
    echo -e "${RED}✗${NC} User Service    :5003  [ERROR]"
fi

if [ $postgres_ok -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PostgreSQL      :5432  [Solo Interno]"
else
    echo -e "${RED}✗${NC} PostgreSQL      :5432  [ERROR]"
fi

echo ""

# Verificar puertos
echo -e "${BLUE}Puertos Escuchando:${NC}"
netstat -tlnp 2>/dev/null | grep -E ":(8080|5001|5002|5003|5432)" | awk '{print "  "$4}' || \
    ss -tlnp 2>/dev/null | grep -E ":(8080|5001|5002|5003|5432)" | awk '{print "  "$4}'

echo ""

# Estado final
if [ $gateway_ok -eq 0 ] && [ $auth_ok -eq 0 ] && [ $admin_ok -eq 0 ] && [ $user_ok -eq 0 ] && [ $postgres_ok -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ TODOS LOS SERVICIOS OPERACIONALES                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}El sistema está listo para recibir peticiones.${NC}"
    echo -e "Punto de entrada: ${BLUE}http://localhost:8080${NC}"
    echo ""
    echo -e "Pruebas disponibles:"
    echo -e "  ${YELLOW}cd services && ./test_admin_service.sh${NC}"
    echo -e "  ${YELLOW}cd services/auth && ./test_auth_service.sh${NC}"
    echo -e "  ${YELLOW}cd services/user && make test${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ ALGUNOS SERVICIOS NO ESTÁN OPERACIONALES          ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Por favor, revisa los servicios marcados con ✗${NC}"
    echo ""
    echo -e "Para iniciar servicios:"
    echo -e "  ${YELLOW}# Desde /services con Makefile${NC}"
    echo -e "  cd services && make start"
    echo ""
    echo -e "  ${YELLOW}# O manualmente:${NC}"
    echo -e "  # PostgreSQL${NC}"
    echo -e "  docker-compose up -d postgres"
    echo ""
    echo -e "  # Auth Service${NC}"
    echo -e "  cd services/auth && make dev"
    echo ""
    echo -e "  # Admin Service${NC}"
    echo -e "  cd services/admin && make dev"
    echo ""
    echo -e "  # User Service${NC}"
    echo -e "  cd services/user && make dev"
    echo ""
    echo -e "  # Gateway${NC}"
    echo -e "  cd services/gateway && make dev"
    echo ""
    exit 1
fi
