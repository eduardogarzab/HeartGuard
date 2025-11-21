#!/bin/bash

# =============================================================================
# HeartGuard Desktop App - Pre-Launch Verification
# =============================================================================

echo "=========================================="
echo "HeartGuard Desktop App - Verificación"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar servicio
check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Verificando $name... "
    response=$(curl -s "$url" 2>&1)
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  URL: $url"
        echo "  Respuesta: $response"
        return 1
    fi
}

errors=0

echo "1. Verificando servicios backend..."
echo ""

# Gateway
check_service "Gateway" "http://localhost:8080/health/" "heartguard-gateway" || ((errors++))

# Realtime Generator
check_service "Realtime Generator" "http://localhost:8080/realtime/health" "realtime-data-generator" || ((errors++))

echo ""
echo "2. Verificando base de datos..."
echo ""

# InfluxDB
check_service "InfluxDB" "http://134.199.204.58:8086/health" "ready for queries" || ((errors++))

echo ""
echo "3. Verificando datos de pacientes..."
echo ""

# Pacientes
patients_response=$(curl -s http://localhost:8080/realtime/patients 2>&1)
patient_count=$(echo "$patients_response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['count'])" 2>/dev/null)

if [ ! -z "$patient_count" ] && [ "$patient_count" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Pacientes siendo monitoreados: $patient_count"
    echo "$patients_response" | python3 -c "import sys, json; d=json.load(sys.stdin); [print(f\"  - {p['name']} (ID: {p['id']})\") for p in d['patients']]" 2>/dev/null
else
    echo -e "${RED}✗${NC} No se encontraron pacientes"
    ((errors++))
fi

echo ""
echo "4. Verificando datos en InfluxDB..."
echo ""

# Query InfluxDB
influx_response=$(curl -s -X POST "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> count()
  |> group()
  |> sum()' 2>&1)

if echo "$influx_response" | grep -q "_value"; then
    data_points=$(echo "$influx_response" | grep "_value" | tail -1 | awk -F',' '{print $8}')
    if [ ! -z "$data_points" ] && [ "$data_points" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Datos en InfluxDB: $data_points puntos en últimos 5 minutos"
    else
        echo -e "${YELLOW}⚠${NC} InfluxDB accesible pero sin datos recientes"
    fi
else
    echo -e "${RED}✗${NC} Error al consultar InfluxDB"
    echo "  Respuesta: $influx_response"
    ((errors++))
fi

echo ""
echo "5. Verificando JAR del desktop app..."
echo ""

if [ -f "target/heartguard-desktop-1.0-SNAPSHOT.jar" ]; then
    jar_size=$(du -h target/heartguard-desktop-1.0-SNAPSHOT.jar | cut -f1)
    echo -e "${GREEN}✓${NC} JAR encontrado: $jar_size"
else
    echo -e "${RED}✗${NC} JAR no encontrado en target/"
    echo "  Ejecuta: mvn clean package"
    ((errors++))
fi

echo ""
echo "=========================================="

if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✓ Todos los servicios están listos${NC}"
    echo ""
    echo "Puedes ejecutar el desktop app con:"
    echo "  ./launch.sh"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Se encontraron $errors problemas${NC}"
    echo ""
    echo "Soluciones:"
    echo "  1. Iniciar servicios: cd /root/HeartGuard/services && make start"
    echo "  2. Compilar JAR: mvn clean package"
    echo "  3. Esperar unos segundos a que se generen datos"
    echo ""
    exit 1
fi
