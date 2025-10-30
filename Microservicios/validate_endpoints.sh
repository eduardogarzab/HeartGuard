#!/usr/bin/env bash
set -euo pipefail

HOST="34.70.7.33"
PROTOCOL="http"
TIMEOUT=10

usage() {
  cat <<USAGE
Uso: $0 [--host HOST] [--protocol http|https] [--timeout SECONDS]
Ejecuta pruebas de salud contra los microservicios HeartGuard verificando respuestas JSON y XML.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="$2"
      shift 2
      ;;
    --protocol)
      PROTOCOL="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento desconocido: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  echo "[ERROR] curl no está disponible en este sistema." >&2
  exit 1
fi

declare -a CHECKS=(
  "Gateway|5000|/gateway/health|GET"
  "Auth|5001|/auth/health|GET"
  "Organization|5002|/organization/health|GET"
  "User|5003|/users/health|GET"
  "Patient|5004|/patients/health|GET"
  "Device|5005|/devices/health|GET"
  "Influx|5006|/influx/health|GET"
  "Inference|5007|/inference/health|GET"
  "Alert|5008|/alerts/health|GET"
  "Notification|5009|/notifications/health|GET"
  "Media|5010|/media/health|GET"
  "Audit|5011|/audit/health|GET"
)

JSON_OK=0
XML_OK=0
JSON_TOTAL=0
XML_TOTAL=0

printf "\n%-15s %-8s %-30s %-6s %-12s %-8s %-8s\n" "Servicio" "Puerto" "Endpoint" "Verbo" "Formato" "HTTP" "Tiempo"
printf '%s\n' "-------------------------------------------------------------------------------------------------------------"

for entry in "${CHECKS[@]}"; do
  IFS='|' read -r NAME PORT PATH METHOD <<<"$entry"
  URL="${PROTOCOL}://${HOST}:${PORT}${PATH}"

  for ACCEPT in "application/json" "application/xml"; do
    FORMAT=$( [[ "$ACCEPT" == "application/json" ]] && echo "JSON" || echo "XML" )
    HTTP_CODE=$(mktemp)
    BODY=$(mktemp)
    START=$(date +%s%3N)
    curl -sS -o "$BODY" \
         -w "%{http_code}" \
         --max-time "$TIMEOUT" \
         -H "Accept: ${ACCEPT}" \
         "${URL}" > "$HTTP_CODE" || true
    END=$(date +%s%3N)
    LATENCY=$(printf '%0.3f' "$(echo "scale=3; ($END - $START)/1000" | bc)")
    CODE=$(cat "$HTTP_CODE")

    STATUS="FAIL"
    if [[ "$CODE" =~ ^2 ]]; then
      STATUS="OK"
      if [[ "$FORMAT" == "JSON" ]]; then
        ((JSON_OK++))
      else
        ((XML_OK++))
      fi
    fi

    if [[ "$FORMAT" == "JSON" ]]; then
      ((JSON_TOTAL++))
    else
      ((XML_TOTAL++))
    fi

    printf "%-15s %-8s %-30s %-6s %-12s %-8s %-8s\n" "$NAME" "$PORT" "$PATH" "$METHOD" "$FORMAT" "$CODE" "$LATENCY"

    rm -f "$HTTP_CODE" "$BODY"
  done

done

printf '%s\n' "-------------------------------------------------------------------------------------------------------------"
printf "Resumen JSON: %d/%d OK\n" "$JSON_OK" "$JSON_TOTAL"
printf "Resumen XML: %d/%d OK\n" "$XML_OK" "$XML_TOTAL"

if [[ "$JSON_OK" -eq "$JSON_TOTAL" && "$XML_OK" -eq "$XML_TOTAL" ]]; then
  echo "Estado general: OK"
else
  echo "Estado general: FALLA"
fi
