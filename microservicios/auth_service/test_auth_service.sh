#!/usr/bin/env bash
set -euo pipefail

service="auth_service"
BASE_URL="${BASE_URL:-http://34.70.7.33}"
BASE_URL="${BASE_URL%/}"

printf '[%s] Checking %s/health...\n' "$service" "$BASE_URL"
curl --fail --silent --show-error "$BASE_URL/health" >/dev/null
printf '[%s] Health check OK.\n' "$service"
