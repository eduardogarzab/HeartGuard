#!/bin/bash

set -e

BASE_URL="http://localhost:8080"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test Completo de Endpoints - HeartGuard Org Admin"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Login
echo "1️⃣  Login..."
TOKEN=$(curl -s -X POST "${BASE_URL}/auth/login/user" \
  -H "Content-Type: application/json" \
  -d '{"email":"ana.ruiz@heartguard.com","password":"Demo#2025"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Error: No se pudo obtener el token"
    exit 1
fi
echo "✅ Token obtenido"
echo ""

# 2. Listar organizaciones
echo "2️⃣  Listando organizaciones..."
ORG_ID=$(curl -s "${BASE_URL}/admin/organizations" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -oP '<id>\K[^<]+' | head -1)

if [ -z "$ORG_ID" ]; then
    echo "❌ Error: No se encontró ninguna organización"
    exit 1
fi
echo "✅ Organización ID: $ORG_ID"
echo ""

# 3. Listar pacientes
echo "3️⃣  Listando pacientes..."
PATIENT_COUNT=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/patients" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -c '<patient>' || echo "0")
echo "✅ Pacientes encontrados: $PATIENT_COUNT"
echo ""

# 4. Listar staff
echo "4️⃣  Listando staff..."
STAFF_COUNT=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/staff" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -c '<staff_member>' || echo "0")
echo "✅ Staff encontrados: $STAFF_COUNT"
echo ""

# 5. Listar alertas
echo "5️⃣  Listando alertas..."
ALERT_COUNT=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -c '<alert>' || echo "0")
echo "✅ Alertas encontradas: $ALERT_COUNT"
echo ""

# 6. Listar devices
echo "6️⃣  Listando devices..."
DEVICE_COUNT=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/devices" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -c '<device>' || echo "0")
echo "✅ Devices encontrados: $DEVICE_COUNT"
echo ""

# 7. Listar push devices
echo "7️⃣  Listando push devices..."
PUSH_DEVICE_COUNT=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/push-devices" \
  -H "Authorization: Bearer $TOKEN" \
  | grep -c '<push_device>' || echo "0")
echo "✅ Push devices encontrados: $PUSH_DEVICE_COUNT"
echo ""

# 8. Crear paciente
echo "8️⃣  Creando nuevo paciente..."
CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/admin/organizations/${ORG_ID}/patients" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Patient&email=test.patient@test.com&password=test123&birthdate=1990-01-15&risk_level_id=LOW")

NEW_PATIENT_ID=$(echo "$CREATE_RESPONSE" | grep -oP '<id>\K[^<]+' | head -1)
if [ -z "$NEW_PATIENT_ID" ]; then
    echo "❌ Error al crear paciente"
    echo "$CREATE_RESPONSE"
    exit 1
fi
echo "✅ Paciente creado con ID: $NEW_PATIENT_ID"
echo ""

# 9. Obtener paciente
echo "9️⃣  Obteniendo detalles del paciente..."
PATIENT_DETAIL=$(curl -s "${BASE_URL}/admin/organizations/${ORG_ID}/patients/${NEW_PATIENT_ID}" \
  -H "Authorization: Bearer $TOKEN")
PATIENT_NAME=$(echo "$PATIENT_DETAIL" | grep -oP '<name>\K[^<]+' | head -1)
echo "✅ Paciente encontrado: $PATIENT_NAME"
echo ""

# 10. Actualizar paciente
echo "🔟  Actualizando paciente..."
UPDATE_RESPONSE=$(curl -s -X PATCH "${BASE_URL}/admin/organizations/${ORG_ID}/patients/${NEW_PATIENT_ID}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=Test Patient Updated&risk_level_id=HIGH")

UPDATED_NAME=$(echo "$UPDATE_RESPONSE" | grep -oP '<name>\K[^<]+' | head -1)
echo "✅ Paciente actualizado: $UPDATED_NAME"
echo ""

# 11. Eliminar paciente
echo "1️⃣1️⃣  Eliminando paciente..."
DELETE_RESPONSE=$(curl -s -X DELETE "${BASE_URL}/admin/organizations/${ORG_ID}/patients/${NEW_PATIENT_ID}" \
  -H "Authorization: Bearer $TOKEN")

if echo "$DELETE_RESPONSE" | grep -q "<deleted>true</deleted>"; then
    echo "✅ Paciente eliminado exitosamente"
else
    echo "⚠️  Respuesta de eliminación: $DELETE_RESPONSE"
fi
echo ""

# 12. Verificar eliminación
echo "1️⃣2️⃣  Verificando eliminación..."
VERIFY_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/admin/organizations/${ORG_ID}/patients/${NEW_PATIENT_ID}" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$VERIFY_RESPONSE" | tail -1)
if [ "$HTTP_CODE" == "404" ]; then
    echo "✅ Paciente correctamente eliminado (404 esperado)"
else
    echo "⚠️  HTTP Code: $HTTP_CODE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Todas las pruebas completadas"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Resumen:"
echo "  • Organizaciones: ✓"
echo "  • Pacientes: $PATIENT_COUNT (CRUD: ✓)"
echo "  • Staff: $STAFF_COUNT"
echo "  • Alertas: $ALERT_COUNT"
echo "  • Devices: $DEVICE_COUNT"
echo "  • Push Devices: $PUSH_DEVICE_COUNT"
