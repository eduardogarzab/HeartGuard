#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
MICRO_DIR="$ROOT_DIR/microservicios"

BASE_URL="${BASE_URL:-http://34.70.7.33}"
BASE_URL="${BASE_URL%/}"
AUTH_URL="${AUTH_URL:-$BASE_URL}"
AUTH_URL="${AUTH_URL%/}"
ADMIN_EMAIL="${ADMIN_EMAIL:-ana.ruiz@heartguard.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Demo#2025}"

services=(
  auth_service
  org_service
  audit_service
  gateway
  media_service
  alert_service
  analytics_service
)

status=0

for service in "${services[@]}"; do
  script_path="$MICRO_DIR/$service/test_${service}.sh"
  if [[ ! -x "$script_path" ]]; then
    printf '[validate] Script no encontrado para %s: %s\n' "$service" "$script_path" >&2
    status=1
    continue
  fi

  printf '\n[validate] Ejecutando %s...\n' "$service"
  if ! (
    cd "$(dirname "$script_path")" && \
    BASE_URL="$BASE_URL" \
    AUTH_URL="$AUTH_URL" \
    ADMIN_EMAIL="$ADMIN_EMAIL" \
    ADMIN_PASSWORD="$ADMIN_PASSWORD" \
    "./$(basename "$script_path")"
  ); then
    result=$?
    printf '[validate] %s fallo con codigo %s.\n' "$service" "$result" >&2
    if [[ $status -eq 0 ]]; then
      status=$result
    fi
  else
    printf '[validate] %s OK.\n' "$service"
  fi
done

exit "$status"
