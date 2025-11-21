#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URLs
DIRECT_URL="http://localhost:5006"
GATEWAY_URL="http://localhost:8080/realtime"

echo "=========================================="
echo "HeartGuard Realtime Data Generator Tests"
echo "=========================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    response=$(curl -s -w "\n%{http_code}" "$url")
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        if [ ! -z "$body" ]; then
            echo "  Response: $(echo $body | python3 -m json.tool 2>/dev/null | head -3 | tr '\n' ' ')"
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        echo "  Response: $body"
    fi
    echo ""
}

echo "=== Direct Service Tests (Port 5006) ==="
echo ""
test_endpoint "$DIRECT_URL/health" "Health Check (Direct)"
test_endpoint "$DIRECT_URL/status" "Status Endpoint (Direct)"
test_endpoint "$DIRECT_URL/patients" "Patients List (Direct)"

echo ""
echo "=== Gateway Tests (Port 8080) ==="
echo ""
test_endpoint "$GATEWAY_URL/health" "Health Check (Gateway)"
test_endpoint "$GATEWAY_URL/status" "Status Endpoint (Gateway)"
test_endpoint "$GATEWAY_URL/patients" "Patients List (Gateway)"

echo ""
echo "=== Worker Status Verification ==="
echo ""

# Get status and check worker is running
status_json=$(curl -s "$GATEWAY_URL/status")
worker_running=$(echo $status_json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['worker']['running'])" 2>/dev/null)
iteration=$(echo $status_json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['worker']['iteration'])" 2>/dev/null)
patient_count=$(echo $status_json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['database']['active_patients'])" 2>/dev/null)

if [ "$worker_running" = "True" ]; then
    echo -e "${GREEN}✓${NC} Worker is running"
    echo "  Iteration: $iteration"
    echo "  Active patients: $patient_count"
else
    echo -e "${RED}✗${NC} Worker is NOT running"
fi

echo ""
echo "=== Data Generation Test ==="
echo ""

# Check InfluxDB for recent data
echo "Querying InfluxDB for recent data..."
influx_response=$(curl -s -X POST "http://134.199.204.58:8086/api/v2/query?org=heartguard" \
  -H "Authorization: Token heartguard-dev-token-change-me" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket: "timeseries")
  |> range(start: -1m)
  |> filter(fn: (r) => r._measurement == "vital_signs")
  |> count()
  |> group()
  |> sum()' 2>&1)

if echo "$influx_response" | grep -q "_value"; then
    data_points=$(echo "$influx_response" | grep "_value" | tail -1 | awk -F',' '{print $8}')
    echo -e "${GREEN}✓${NC} Data is being written to InfluxDB"
    echo "  Data points in last minute: $data_points"
else
    echo -e "${YELLOW}⚠${NC} Could not verify InfluxDB data"
fi

echo ""
echo "=========================================="
echo "Test suite completed"
echo "=========================================="
