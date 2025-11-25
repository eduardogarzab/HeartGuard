#!/bin/bash

# IDs de prueba (ajustar según tu BD)
ORG_ID="c460774d-2af7-42ee-a146-4ccd5a9069b0"
PATIENT_ID="8c9436b4-f085-405f-a3d2-87cb1d1cf097"
USER_ID="66569396-bba3-41a9-a32b-6a8abfe361df"

echo "=== Test 1: Obtener alertas del paciente ==="
ALERT_RESPONSE=$(curl -s "http://localhost:5003/orgs/${ORG_ID}/patients/${PATIENT_ID}/alerts?limit=1")
echo "$ALERT_RESPONSE" | python3 -m json.tool

# Extraer alert_id si existe
ALERT_ID=$(echo "$ALERT_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); alerts=d.get('data',{}).get('alerts',[]); print(alerts[0]['id'] if alerts else '')" 2>/dev/null)

if [ -z "$ALERT_ID" ]; then
    echo ""
    echo "⚠️ No se encontraron alertas para este paciente. Prueba con otros IDs."
    exit 1
fi

echo ""
echo "✅ Alert ID encontrado: $ALERT_ID"
echo ""

echo "=== Test 2: Acknowledge alerta ==="
curl -s -X POST "http://localhost:5003/orgs/${ORG_ID}/patients/${PATIENT_ID}/alerts/${ALERT_ID}/acknowledge" \
    -H "Content-Type: application/json" \
    -d "{\"note\": \"Alerta reconocida desde script de prueba\"}" | python3 -m json.tool

echo ""
echo ""

echo "=== Test 3: Resolve alerta ==="
curl -s -X POST "http://localhost:5003/orgs/${ORG_ID}/patients/${PATIENT_ID}/alerts/${ALERT_ID}/resolve" \
    -H "Content-Type: application/json" \
    -d "{\"outcome\": \"false_positive\", \"note\": \"Falso positivo - prueba desde script\"}" | python3 -m json.tool

echo ""
echo "✅ Pruebas completadas"
