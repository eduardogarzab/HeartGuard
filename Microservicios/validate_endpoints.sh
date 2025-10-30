#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${GATEWAY_BASE_URL:-http://localhost:5000}
ADMIN_EMAIL=${VALIDATE_ADMIN_EMAIL:-admin@heartguard.io}
ADMIN_PASSWORD=${VALIDATE_ADMIN_PASSWORD:-ChangeMe123!}
TMP_DIR=$(mktemp -d)
SUMMARY_JSON="$TMP_DIR/summary.json"
SUMMARY_XML="$TMP_DIR/summary.xml"

declare -A RESULTS

echo "[INFO] Autenticando contra ${BASE_URL}"
LOGIN_JSON=$(curl -s -w "\n%{http_code}\n%{time_total}" -H "Accept: application/json" -H "Content-Type: application/json" -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASSWORD}\"}" "${BASE_URL}/auth/login" || true)
LOGIN_BODY=$(echo "$LOGIN_JSON" | head -n -2)
LOGIN_CODE=$(echo "$LOGIN_JSON" | tail -n 2 | head -n 1)
LOGIN_LAT=$(echo "$LOGIN_JSON" | tail -n 1)
if [[ "$LOGIN_CODE" != "200" ]]; then
  echo "[WARN] Login falló (HTTP $LOGIN_CODE). Servicios protegidos se validarán sin token."
  ACCESS_TOKEN=""
else
  ACCESS_TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token',''))" 2>/dev/null || true)
  echo "[INFO] Login exitoso en ${LOGIN_LAT}s"
fi

HEADER_AUTH=()
if [[ -n "$ACCESS_TOKEN" ]]; then
  HEADER_AUTH=(-H "Authorization: Bearer ${ACCESS_TOKEN}")
fi

declare -a ENDPOINTS=(
  "Gateway Health|/gateway/health|GET|public"
  "Auth Profile|/auth/profile|GET|protected"
  "Organization Get|/organization|GET|protected"
  "User Self|/users/me|GET|protected"
  "Media List|/media/items|GET|protected"
  "Influx Health|/timeseries/health|GET|public"
  "Audit Health|/audit/health|GET|protected"
)

echo "SERVICE|FORMAT|HTTP_CODE|LATENCY_S|STATUS"
for entry in "${ENDPOINTS[@]}"; do
  IFS='|' read -r NAME PATH METHOD ACCESS <<<"$entry"
  AUTH_HEADERS=()
  if [[ "$ACCESS" == "protected" && -n "$ACCESS_TOKEN" ]]; then
    AUTH_HEADERS=(${HEADER_AUTH[@]})
  fi
  for FORMAT in json xml; do
    ACCEPT="application/${FORMAT}"
    CURL_OUT=$(curl -s -w "\n%{http_code}\n%{time_total}" -X "$METHOD" -H "Accept: ${ACCEPT}" "${AUTH_HEADERS[@]}" "${BASE_URL}${PATH}" || true)
    BODY=$(echo "$CURL_OUT" | head -n -2)
    CODE=$(echo "$CURL_OUT" | tail -n 2 | head -n 1)
    LAT=$(echo "$CURL_OUT" | tail -n 1)
    STATUS="FAIL"
    if [[ "$CODE" =~ ^2 ]]; then
      STATUS="OK"
    fi
    echo "${NAME}|${FORMAT^^}|${CODE}|${LAT}|${STATUS}"
    RESULTS["${NAME}_${FORMAT}"]="$CODE|$LAT|$STATUS"
    if [[ "$FORMAT" == "json" ]]; then
      echo "$BODY" > "$SUMMARY_JSON"
    else
      echo "$BODY" > "$SUMMARY_XML"
    fi
  done
done

echo "\nResumen por servicio:"
for entry in "${ENDPOINTS[@]}"; do
  IFS='|' read -r NAME PATH METHOD ACCESS <<<"$entry"
  JSON_STATUS=${RESULTS["${NAME}_json"]##*|}
  XML_STATUS=${RESULTS["${NAME}_xml"]##*|}
  if [[ "$JSON_STATUS" == "OK" && "$XML_STATUS" == "OK" ]]; then
    echo "[OK] ${NAME}"
  else
    echo "[FAIL] ${NAME}"
  fi
done

echo "\nPara más detalle revise los archivos temporales: ${SUMMARY_JSON} ${SUMMARY_XML}"
