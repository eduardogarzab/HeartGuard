#!/usr/bin/env bash
set -euo pipefail

service="gateway"
BASE_URL="${BASE_URL:-http://34.70.7.33}"
BASE_URL="${BASE_URL%/}"
AUTH_URL="${AUTH_URL:-$BASE_URL}"
AUTH_URL="${AUTH_URL%/}"
ADMIN_EMAIL="${ADMIN_EMAIL:-ana.ruiz@heartguard.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Demo#2025}"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  elif command -v python >/dev/null 2>&1; then
    echo python
  else
    return 1
  fi
}

PYTHON_BIN="$(find_python)"
if [[ -z "$PYTHON_BIN" ]]; then
  printf '[%s] Python no disponible en el PATH.\n' "$service" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LOGIN_PAYLOAD="$TMP_DIR/login_payload.json"
"$PYTHON_BIN" - "$LOGIN_PAYLOAD" <<'PY'
import json
import os
import sys

payload = {
    "email": os.environ.get("ADMIN_EMAIL", "ana.ruiz@heartguard.com"),
    "password": os.environ.get("ADMIN_PASSWORD", "Demo#2025"),
}
with open(sys.argv[1], "w", encoding="utf-8") as fh:
    json.dump(payload, fh, separators=(",", ":"))
PY

LOGIN_RESPONSE="$TMP_DIR/login_response.json"
curl --fail --silent --show-error \
  -X POST "$AUTH_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  --data-binary @"$LOGIN_PAYLOAD" \
  -o "$LOGIN_RESPONSE"

ACCESS_TOKEN="$("$PYTHON_BIN" - "$LOGIN_RESPONSE" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding='utf-8'))
print(data['data']['access_token'])
PY
)"
ACCESS_TOKEN="${ACCESS_TOKEN//$'\r'/}"
ACCESS_TOKEN="${ACCESS_TOKEN//$'\n'/}"
if [[ -z "$ACCESS_TOKEN" ]]; then
  printf '[%s] No se pudo obtener access_token.\n' "$service" >&2
  exit 1
fi

printf '[%s] Checking %s/health...\n' "$service" "$BASE_URL"
curl --fail --silent --show-error \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/health" >/dev/null
printf '[%s] Health check OK.\n' "$service"
