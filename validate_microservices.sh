#!/usr/bin/env bash
# shellcheck disable=SC2034

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
MICRO_DIR="$REPO_ROOT/microservicios"
LOG_DIR="$MICRO_DIR/validation_logs"
REPORT="$LOG_DIR/validation_report.txt"
CURL_ERRORS="$LOG_DIR/curl_errors.log"

ADMIN_EMAIL="ana.ruiz@heartguard.com"
ADMIN_PASSWORD="Demo#2025"
POSTGRES_HOST="34.70.7.33"
POSTGRES_PORT="5432"
REDIS_PORT="6379"

PASS_TOTAL=0
FAIL_TOTAL=0
TEST_COUNTER=0
LAST_RESULT="UNKNOWN"
EXIT_CODE=0
ABORT_TESTS=0

AUTH_PORT="${AUTH_PORT:-5001}"
ORG_PORT="${ORG_PORT:-5002}"
AUDIT_PORT="${AUDIT_PORT:-5006}"
GATEWAY_PORT="${GATEWAY_PORT:-5000}"
MEDIA_PORT="${MEDIA_PORT:-5007}"
CHOSEN_GATEWAY_NOTE=""

ORG_PID_KILLED=0

set_service_pid() {
  local tag="$1"
  local pid="$2"
  printf -v "SERVICE_PID_${tag}" '%s' "$pid"
}

get_service_pid() {
  local tag="$1"
  local var="SERVICE_PID_${tag}"
  printf '%s' "${!var:-}"
}

clear_service_pid() {
  local tag="$1"
  unset "SERVICE_PID_${tag}"
}

ensure_port_free() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    log "Port $port" "lsof no disponible; omitiendo liberacion" "stderr"
    return 0
  fi
  local pids
  if pids="$(lsof -ti tcp:"$port" 2>/dev/null)" && [[ -n "$pids" ]]; then
    while IFS= read -r pid; do
      if kill "$pid" >/dev/null 2>&1; then
        log "Port $port" "Proceso $pid detenido" "stderr"
      fi
    done <<<"$pids"
    sleep 1
  fi
}

port_available() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  if lsof -ti tcp:"$port" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  local key="$1"
  local value="$2"
  local ts
  ts="$(timestamp)"
  local line="[$ts] [INFO] $key: $value"
  if [[ "$stream" == "stderr" ]]; then
    printf '%s\n' "$line" >&2
  else
    printf '%s\n' "$line"
  fi
  printf '%s\n' "$line" >>"$REPORT"
}

record_pass() {
  local msg="$1"
  local info="$2"
  local ts
  ts="$(timestamp)"
  PASS_TOTAL=$((PASS_TOTAL + 1))
  echo "[$ts] [PASS] $msg - $info"
  echo "[$ts] [PASS] $msg - $info" >>"$REPORT"
}

record_fail() {
  local msg="$1"
  local info="$2"
  local ts
  ts="$(timestamp)"
  FAIL_TOTAL=$((FAIL_TOTAL + 1))
  echo "[$ts] [FAIL] $msg - $info"
  echo "[$ts] [FAIL] $msg - $info" >>"$REPORT"
}

log_response() {
  local body_file="$1"
  if [[ -f "$body_file" && -n "${PYTHON_BOOTSTRAP:-}" ]]; then
    local raw
    raw="$("$PYTHON_BOOTSTRAP" - "$body_file" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = path.read_text(encoding='utf-8', errors='replace')
except Exception:
    data = ''
if len(data) > 800:
    data = data[:800] + '...'
print(data)
PY
)"
    printf '    Body: %s\n' "$raw" >>"$REPORT"
  fi
}

find_python() {
  local candidates=(python3 python py)
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BOOTSTRAP="$candidate"
      log "Python" "Usando interprete $candidate"
      return 0
    fi
  done
  record_fail "Python" "No se encontro interprete compatible"
  ABORT_TESTS=1
  return 1
}

setup_service_env() {
  local service_key="$1"
  local service_dir="$2"
  local venv_dir="$service_dir/.venv"
  local setup_log="$LOG_DIR/${service_key}_venv.log"
  local pip_log="$LOG_DIR/${service_key}_pip.log"

  log "Setup $service_key" "Creando entorno virtual"
  if [[ ! -d "$venv_dir" ]]; then
    "$PYTHON_BOOTSTRAP" -m venv "$venv_dir" >>"$setup_log" 2>&1 || {
      record_fail "Setup $service_key" "Fallo creando entorno virtual (ver ${service_key}_venv.log)"
      return 1
    }
  fi

  local venv_python="$venv_dir/bin/python"
  if [[ ! -x "$venv_python" ]]; then
    record_fail "Setup $service_key" "Python del entorno no encontrado"
    return 1
  fi

  local req_file="$service_dir/requirements.txt"
  if [[ -f "$req_file" ]]; then
    log "Setup $service_key" "Instalando dependencias"
    "$venv_python" -m pip install --upgrade pip >>"$pip_log" 2>&1 || {
      record_fail "Setup $service_key" "Fallo instalando dependencias (ver ${service_key}_pip.log)"
      return 1
    }
    "$venv_python" -m pip install -r "$req_file" >>"$pip_log" 2>&1 || {
      record_fail "Setup $service_key" "Fallo instalando dependencias (ver ${service_key}_pip.log)"
      return 1
    }
  else
    log "Setup $service_key" "No se encontro requirements.txt"
  fi

  record_pass "Setup $service_key" "Entorno virtual listo"
  return 0
}

check_dependency() {
  local name="$1"
  local host="$2"
  local port="$3"
  if "$PYTHON_BOOTSTRAP" - "$host" "$port" <<'PY' >/dev/null 2>&1; then
import socket, sys

host = sys.argv[1]
port = int(sys.argv[2])
with socket.create_connection((host, port), timeout=5):
    pass
PY
    record_pass "Conectividad $name" "Puerto $port accesible"
  else
    record_fail "Conectividad $name" "Fallo al alcanzar $host:$port"
  fi
}

verify_postgres() {
  local auth_python="$MICRO_DIR/auth_service/.venv/bin/python"
  if [[ ! -x "$auth_python" ]]; then
    record_fail "Conexion Postgres" "Python del servicio auth no disponible"
    return 1
  fi
  if (cd "$MICRO_DIR/auth_service" && "$auth_python" - <<'PY' >>"$LOG_DIR/postgres_check.log" 2>&1); then
from db import get_conn, put_conn
conn = get_conn()
cur = conn.cursor()
cur.execute('SELECT 1')
cur.fetchone()
put_conn(conn)
PY
    record_pass "Conexion Postgres" "Consulta SELECT 1 exitosa"
    return 0
  else
    record_fail "Conexion Postgres" "Fallo verificacion (ver postgres_check.log)"
    return 1
  fi
}

verify_redis() {
  local auth_python="$MICRO_DIR/auth_service/.venv/bin/python"
  if [[ ! -x "$auth_python" ]]; then
    record_fail "Conexion Redis" "Python del servicio auth no disponible"
    return 1
  fi
  if (cd "$MICRO_DIR/auth_service" && "$auth_python" - <<'PY' >>"$LOG_DIR/redis_check.log" 2>&1); then
from redis_client import get_redis
client = get_redis()
client.ping()
PY
    record_pass "Conexion Redis" "Ping exitoso"
    return 0
  else
    record_fail "Conexion Redis" "Fallo verificacion (ver redis_check.log)"
    return 1
  fi
}

start_service() {
  local tag="$1"
  local service_dir="$2"
  local python_bin="$3"
  local port="${4:-}"
  local stdout_file="$LOG_DIR/${tag}_stdout.log"
  local stderr_file="$LOG_DIR/${tag}_stderr.log"

  : >"$stdout_file"
  : >"$stderr_file"

  if [[ ! -x "$python_bin" ]]; then
    record_fail "Start $tag" "Interprete no encontrado"
    return 1
  fi

  if [[ -n "$port" ]]; then
    ensure_port_free "$port"
  fi

  local shared_env_file="$MICRO_DIR/.env"
  if [[ -f "$shared_env_file" ]]; then
    while IFS= read -r line; do
      if [[ ! "$line" =~ ^\s*# && -n "$line" ]]; then
        export "$line"
      fi
    done < "$shared_env_file"
  fi

  local service_env_file="$service_dir/.env"
  if [[ -f "$service_env_file" ]]; then
    while IFS= read -r line; do
      if [[ ! "$line" =~ ^\s*# && -n "$line" ]]; then
        export "$line"
      fi
    done < "$service_env_file"
  fi

  log "Start $tag" "Lanzando servicio"
  (
    cd "$service_dir" || exit 1
    nohup "$python_bin" app.py >>"$stdout_file" 2>>"$stderr_file" &
    echo $!
  ) >"$LOG_DIR/start_${tag}.log" 2>&1

  local pid
  pid="$(tail -n 1 "$LOG_DIR/start_${tag}.log" 2>/dev/null)"
  if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
    record_fail "Start $tag" "No se pudo iniciar (ver start_${tag}.log)"
    return 1
  fi

  set_service_pid "$tag" "$pid"
  log "Start $tag" "PID $pid"
  sleep 6
  if kill -0 "$pid" >/dev/null 2>&1; then
    record_pass "Start $tag" "Servicio activo"
    return 0
  else
    record_fail "Start $tag" "Proceso finalizo prematuramente (ver stderr)"
    return 1
  fi
}

stop_service() {
  local tag="$1"
  local pid
  pid="$(get_service_pid "$tag")"
  if [[ -n "$pid" ]]; then
    if kill "$pid" >/dev/null 2>&1; then
      log "Stop $tag" "PID $pid detenido"
    fi
    clear_service_pid "$tag"
  fi
}

http_test() {
  local name="$1"
  local url="$2"
  local expected="$3"
  TEST_COUNTER=$((TEST_COUNTER + 1))
  local tmp_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  local http_code
  http_code="$(curl -s -o "$tmp_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 "$url" 2>>"$CURL_ERRORS")"
  assert_status "$name" "$http_code" "$expected" "$tmp_file"
}

assert_status() {
  local name="$1"
  local actual="$2"
  local expected="$3"
  local body_file="$4"
  if [[ "$actual" == "$expected" ]]; then
    LAST_RESULT="PASS"
    record_pass "$name" "HTTP $actual"
  else
    LAST_RESULT="FAIL"
    record_fail "$name" "HTTP $actual (esperado $expected)"
    log_response "$body_file"
  fi
}

run_tests() {
  http_test "Health auth_service" "http://127.0.0.1:${AUTH_PORT}/health" "200"
  http_test "Health org_service" "http://127.0.0.1:${ORG_PORT}/health" "200"
  http_test "Health audit_service" "http://127.0.0.1:${AUDIT_PORT}/health" "200"
  http_test "Health gateway" "http://127.0.0.1:${GATEWAY_PORT}/health" "200"

  # signal_service tests removed

  local login_payload="$LOG_DIR/payload_login.json"
  "$PYTHON_BOOTSTRAP" - "$login_payload" "$ADMIN_EMAIL" "$ADMIN_PASSWORD" <<'PY'
import json, sys
payload = {"email": sys.argv[2], "password": sys.argv[3]}
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    json.dump(payload, fh, separators=(',', ':'))
PY

  TEST_COUNTER=$((TEST_COUNTER + 1))
  local login_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  local http_code
  http_code="$(curl -s -o "$login_file" -w '%{http_code}' --connect-timeout 15 --max-time 30 -X POST "http://127.0.0.1:${AUTH_PORT}/v1/auth/login" -H "Content-Type: application/json" --data-binary "@$login_payload" 2>>"$CURL_ERRORS")"
  assert_status "Auth login directo" "$http_code" "200" "$login_file"

  if [[ "$LAST_RESULT" == "PASS" ]]; then
    AUTH_ACCESS_TOKEN="$("$PYTHON_BOOTSTRAP" - "$login_file" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    print(data['data']['access_token'])
except Exception:
    pass
PY
)"
    AUTH_REFRESH_TOKEN="$("$PYTHON_BOOTSTRAP" - "$login_file" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    print(data['data']['refresh_token'])
except Exception:
    pass
PY
)"
    AUTH_ACCESS_TOKEN="${AUTH_ACCESS_TOKEN//$'\r'/}"
    AUTH_ACCESS_TOKEN="${AUTH_ACCESS_TOKEN//$'\n'/}"
    AUTH_REFRESH_TOKEN="${AUTH_REFRESH_TOKEN//$'\r'/}"
    AUTH_REFRESH_TOKEN="${AUTH_REFRESH_TOKEN//$'\n'/}"
  fi

  if [[ -z "${AUTH_ACCESS_TOKEN:-}" ]]; then
    record_fail "Auth refresh" "No hay token de acceso"
  else
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local refresh_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$refresh_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:${AUTH_PORT}/v1/auth/refresh" -H "Authorization: Bearer ${AUTH_REFRESH_TOKEN:-}" 2>>"$CURL_ERRORS")"
    assert_status "Auth refresh" "$http_code" "200" "$refresh_file"
  fi

  if [[ -n "${AUTH_ACCESS_TOKEN:-}" ]]; then
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local me_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$me_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -H "Authorization: Bearer ${AUTH_ACCESS_TOKEN:-}" "http://127.0.0.1:${AUTH_PORT}/v1/users/me" 2>>"$CURL_ERRORS")"
    assert_status "Auth users/me" "$http_code" "200" "$me_file"
  fi

  TEST_COUNTER=$((TEST_COUNTER + 1))
  local gw_login_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$gw_login_file" -w '%{http_code}' --connect-timeout 15 --max-time 30 -X POST "http://127.0.0.1:${GATEWAY_PORT}/v1/auth/login" -H "Content-Type: application/json" --data-binary "@$login_payload" 2>>"$CURL_ERRORS")"
  assert_status "Gateway login" "$http_code" "200" "$gw_login_file"

  if [[ "$LAST_RESULT" == "PASS" ]]; then
    GW_ACCESS_TOKEN="$("$PYTHON_BOOTSTRAP" - "$gw_login_file" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    print(data['data']['access_token'])
except Exception:
    pass
PY
)"
    GW_ACCESS_TOKEN="${GW_ACCESS_TOKEN//$'\r'/}"
    GW_ACCESS_TOKEN="${GW_ACCESS_TOKEN//$'\n'/}"
  fi

  if [[ -n "${GW_ACCESS_TOKEN:-}" ]]; then
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local gw_org_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$gw_org_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -H "Authorization: Bearer ${GW_ACCESS_TOKEN:-}" "http://127.0.0.1:${GATEWAY_PORT}/v1/orgs/me" 2>>"$CURL_ERRORS")"
    assert_status "Gateway orgs/me" "$http_code" "200" "$gw_org_file"
    if [[ "$LAST_RESULT" == "PASS" ]]; then
      PRIMARY_ORG_ID="$("$PYTHON_BOOTSTRAP" - "$gw_org_file" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    orgs = data['data']['organizations']
    if orgs:
        print(orgs[0]['id'])
except Exception:
    pass
PY
)"
      PRIMARY_ORG_ID="${PRIMARY_ORG_ID//$'\r'/}"
      PRIMARY_ORG_ID="${PRIMARY_ORG_ID//$'\n'/}"
    fi
  fi

  if [[ -n "${GW_ACCESS_TOKEN:-}" && -n "${PRIMARY_ORG_ID:-}" ]]; then
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local gw_org_detail="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$gw_org_detail" -w '%{http_code}' --connect-timeout 10 --max-time 20 -H "Authorization: Bearer ${GW_ACCESS_TOKEN:-}" "http://127.0.0.1:${GATEWAY_PORT}/v1/orgs/${PRIMARY_ORG_ID}" 2>>"$CURL_ERRORS")"
    assert_status "Gateway org detalle" "$http_code" "200" "$gw_org_detail"
  fi

  if [[ -n "${GW_ACCESS_TOKEN:-}" ]]; then
    local audit_payload="$LOG_DIR/payload_audit.json"
    "$PYTHON_BOOTSTRAP" - "$audit_payload" "$ADMIN_EMAIL" <<'PY'
import json, sys
payload = {
    "action": "validation_probe",
    "source": "validate_script",
    "actor": sys.argv[2],
    "details": {"message": "test entry"},
}
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    json.dump(payload, fh, separators=(',', ':'))
PY
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local audit_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$audit_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:${GATEWAY_PORT}/v1/audit" -H "Authorization: Bearer ${GW_ACCESS_TOKEN:-}" -H "Content-Type: application/json" --data-binary "@$audit_payload" 2>>"$CURL_ERRORS")"
    assert_status "Gateway audit log" "$http_code" "201" "$audit_file"
  fi

  if [[ -n "${GW_ACCESS_TOKEN:-}" && -n "${PRIMARY_ORG_ID:-}" ]]; then
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local forbidden_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$forbidden_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -H "Authorization: Bearer ${GW_ACCESS_TOKEN:-}" "http://127.0.0.1:${GATEWAY_PORT}/v1/orgs/00000000-0000-0000-0000-000000000000" 2>>"$CURL_ERRORS")"
    assert_status "Gateway org inexistente" "$http_code" "403" "$forbidden_file"
  fi

  local invalid_payload="$LOG_DIR/payload_login_invalid.json"
  "$PYTHON_BOOTSTRAP" - "$invalid_payload" "$ADMIN_EMAIL" <<'PY'
import json, sys
payload = {"email": sys.argv[2]}
with open(sys.argv[1], 'w', encoding='utf-8') as fh:
    json.dump(payload, fh, separators=(',', ':'))
PY
  TEST_COUNTER=$((TEST_COUNTER + 1))
  local invalid_file="$LOG_DIR/test_${TEST_COUNTER}.json"
  http_code="$(curl -s -o "$invalid_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:${AUTH_PORT}/v1/auth/login" -H "Content-Type: application/json" --data-binary "@$invalid_payload" 2>>"$CURL_ERRORS")"
  assert_status "Auth login incompleto" "$http_code" "401" "$invalid_file"
}

degradation_test() {
  local org_pid
  org_pid="$(get_service_pid ORG)"
  if [[ -n "$org_pid" && -n "${GW_ACCESS_TOKEN:-}" ]]; then
    log "Degradacion" "Deteniendo org_service (PID $org_pid)"
    if kill "$org_pid" >>"$LOG_DIR/stop_org_service.log" 2>&1; then
      ORG_PID_KILLED=1
      clear_service_pid ORG
    fi
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local tmp_file="$LOG_DIR/test_${TEST_COUNTER}.json"
    local http_code
  http_code="$(curl -s -o "$tmp_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 -H "Authorization: Bearer ${GW_ACCESS_TOKEN:-}" "http://127.0.0.1:${GATEWAY_PORT}/v1/orgs/me" 2>>"$CURL_ERRORS")"
    assert_status "Gateway routing with org_service offline" "$http_code" "503" "$tmp_file"
  else
    record_fail "Gateway routing with org_service offline" "No se pudo simular degradacion (PID o token ausente)"
  fi

  if [[ -z "${GW_ACCESS_TOKEN:-}" ]]; then
    record_fail "Gateway routing without token" "No se pudo evaluar respuesta sin token por falla previa"
  else
    TEST_COUNTER=$((TEST_COUNTER + 1))
    local tmp_file="$LOG_DIR/test_${TEST_COUNTER}.json"
    local http_code
  http_code="$(curl -s -o "$tmp_file" -w '%{http_code}' --connect-timeout 10 --max-time 20 "http://127.0.0.1:${GATEWAY_PORT}/v1/orgs/me" 2>>"$CURL_ERRORS")"
    assert_status "Gateway without token" "$http_code" "401" "$tmp_file"
  fi
}

cleanup() {
  log "Cleanup" "Deteniendo microservicios"
  stop_service AUTH
  stop_service ORG
  stop_service AUDIT
  stop_service SIGNAL
  stop_service GATEWAY
  stop_service MEDIA
}

finalize() {
  local ts
  ts="$(timestamp)"
  echo "==================================================" >>"$REPORT"
  echo "Validation run finished at $ts" >>"$REPORT"
  echo "Totals: PASS=$PASS_TOTAL FAIL=$FAIL_TOTAL" >>"$REPORT"
  echo "==================================================" >>"$REPORT"
  echo "=================================================="
  echo "Validacion completada. PASS=$PASS_TOTAL FAIL=$FAIL_TOTAL"
  if (( FAIL_TOTAL > 0 )); then
    EXIT_CODE=1
  else
    EXIT_CODE=0
  fi
}

main() {
  local start_ts
  start_ts="$(timestamp)"
  echo "Validation run started at $start_ts" >"$REPORT"
  echo "==================================================" >>"$REPORT"

  log "Repositorio" "$REPO_ROOT"
  log "Logs" "$LOG_DIR"

  export ADMIN_EMAIL ADMIN_PASSWORD POSTGRES_HOST POSTGRES_PORT REDIS_PORT
  export REDIS_HOST="$POSTGRES_HOST"

  find_python || true
  if (( ABORT_TESTS == 1 )); then
    finalize
    exit $EXIT_CODE
  fi

  setup_service_env "auth" "$MICRO_DIR/auth_service" || ABORT_TESTS=1
  setup_service_env "org" "$MICRO_DIR/org_service" || ABORT_TESTS=1
  setup_service_env "audit" "$MICRO_DIR/audit_service" || ABORT_TESTS=1
  setup_service_env "gateway" "$MICRO_DIR/gateway" || ABORT_TESTS=1
  setup_service_env "media" "$MICRO_DIR/media_service" || ABORT_TESTS=1

  if (( ABORT_TESTS == 0 )); then
    check_dependency "PostgreSQL" "$POSTGRES_HOST" "$POSTGRES_PORT"
    check_dependency "Redis" "$POSTGRES_HOST" "$REDIS_PORT"

    verify_postgres || ABORT_TESTS=1
    verify_redis || ABORT_TESTS=1
  fi

  if (( ABORT_TESTS == 0 )); then
    # signal_service DB init/seed removed
  fi

  if (( ABORT_TESTS == 0 )); then
    local auth_python="$MICRO_DIR/auth_service/.venv/bin/python"
    local org_python="$MICRO_DIR/org_service/.venv/bin/python"
    local audit_python="$MICRO_DIR/audit_service/.venv/bin/python"
    local gateway_python="$MICRO_DIR/gateway/.venv/bin/python"
    local media_python="$MICRO_DIR/media_service/.venv/bin/python"

    GATEWAY_PORT="$(choose_gateway_port "$GATEWAY_PORT" 5050 5500 6000)"
    if [[ -n "$CHOSEN_GATEWAY_NOTE" ]]; then
      log "Gateway" "$CHOSEN_GATEWAY_NOTE"
    fi
  export AUTH_SERVICE_PORT="$AUTH_PORT"
  export ORG_SERVICE_PORT="$ORG_PORT"
  export AUDIT_SERVICE_PORT="$AUDIT_PORT"
    export GATEWAY_SERVICE_PORT="$GATEWAY_PORT"
  export AUTH_SERVICE_URL="http://127.0.0.1:${AUTH_PORT}"
  export ORG_SERVICE_URL="http://127.0.0.1:${ORG_PORT}"
  export AUDIT_SERVICE_URL="http://127.0.0.1:${AUDIT_PORT}"

    start_service AUTH "$MICRO_DIR/auth_service" "$auth_python" "$AUTH_PORT" || ABORT_TESTS=1
    start_service ORG "$MICRO_DIR/org_service" "$org_python" "$ORG_PORT" || ABORT_TESTS=1
    start_service AUDIT "$MICRO_DIR/audit_service" "$audit_python" "$AUDIT_PORT" || ABORT_TESTS=1
    start_service GATEWAY "$MICRO_DIR/gateway" "$gateway_python" "$GATEWAY_PORT" || ABORT_TESTS=1
    start_service MEDIA "$MICRO_DIR/media_service" "$media_python" "$MEDIA_PORT" || ABORT_TESTS=1
  fi

  if (( ABORT_TESTS == 0 )); then
    run_tests
    degradation_test
  fi

  cleanup
  finalize
  exit $EXIT_CODE
}

main "$@"
