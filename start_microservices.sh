#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/.logs"
PID_DIR="$ROOT_DIR/.pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

SHARED_ENV="$ROOT_DIR/microservicios/.env"
if [ -f "$SHARED_ENV" ]; then
  set -a
  # Export shared configuration expected by the microservices
  source "$SHARED_ENV"
  set +a
fi

resolve_python() {
  for candidate in "$@"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      echo "$candidate"
      return 0
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  echo "No Python interpreter found" >&2
  exit 1
}

start_service() {
  local name="$1"
  local script_path="$2"
  local python_bin="$3"
  local log_file="$LOG_DIR/${name}.log"
  local pid_file="$PID_DIR/${name}.pid"

  if [ ! -f "$script_path" ]; then
    echo "[WARN] No se encontró el script $script_path" >&2
    return 1
  fi

  if [ -f "$pid_file" ]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if [ -n "$existing_pid" ] && ps -p "$existing_pid" >/dev/null 2>&1; then
      echo "[INFO] $name ya se está ejecutando con PID $existing_pid"
      return 0
    fi
  fi

  echo "[INFO] Iniciando $name con $python_bin"
  nohup "$python_bin" "$script_path" >>"$log_file" 2>&1 &
  local pid=$!
  echo "$pid" >"$pid_file"
  echo "[INFO] $name listo (PID $pid). Logs: $log_file"
}

AUTH_CANDIDATES=(
  "$ROOT_DIR/microservicios/auth_service/.venv/bin/python"
  "$ROOT_DIR/.venv/bin/python"
  "${HEARTGUARD_PYTHON:-}"
  "/tmp/heartguard-test-venv/bin/python"
)
ORG_CANDIDATES=(
  "$ROOT_DIR/microservicios/org_service/.venv/bin/python"
  "$ROOT_DIR/microservicios/auth_service/.venv/bin/python"
  "$ROOT_DIR/.venv/bin/python"
  "${HEARTGUARD_PYTHON:-}"
  "/tmp/heartguard-test-venv/bin/python"
)
GATEWAY_CANDIDATES=(
  "$ROOT_DIR/microservicios/gateway/.venv/bin/python"
  "$ROOT_DIR/microservicios/auth_service/.venv/bin/python"
  "$ROOT_DIR/.venv/bin/python"
  "${HEARTGUARD_PYTHON:-}"
  "/tmp/heartguard-test-venv/bin/python"
)
AUDIT_CANDIDATES=(
  "$ROOT_DIR/microservicios/audit_service/.venv/bin/python"
  "$ROOT_DIR/.venv/bin/python"
  "${HEARTGUARD_PYTHON:-}"
  "/tmp/heartguard-test-venv/bin/python"
)

AUTH_PYTHON="$(resolve_python "${AUTH_CANDIDATES[@]}")"
ORG_PYTHON="$(resolve_python "${ORG_CANDIDATES[@]}")"
GATEWAY_PYTHON="$(resolve_python "${GATEWAY_CANDIDATES[@]}")"
AUDIT_PYTHON="$(resolve_python "${AUDIT_CANDIDATES[@]}")"

start_service "auth_service" "$ROOT_DIR/microservicios/auth_service/app.py" "$AUTH_PYTHON"
start_service "org_service" "$ROOT_DIR/microservicios/org_service/app.py" "$ORG_PYTHON"
start_service "gateway" "$ROOT_DIR/microservicios/gateway/app.py" "$GATEWAY_PYTHON"
start_service "audit_service" "$ROOT_DIR/microservicios/audit_service/app.py" "$AUDIT_PYTHON"

echo
cat <<'EOF'
Servicios en background. Pruebas rápidas:
  curl -s -w '\n%{http_code}\n' http://localhost:5001/health
  curl -s -w '\n%{http_code}\n' http://localhost:5002/health
  curl -s -w '\n%{http_code}\n' http://localhost:5000/health
  curl -s -w '\n%{http_code}\n' http://localhost:5006/health

Comandos útiles:
  tail -f .logs/auth_service.log
  tail -f .logs/org_service.log
  tail -f .logs/gateway.log
  tail -f .logs/audit_service.log

Para detener:
  if [ -f .pids/auth_service.pid ]; then kill "$(cat .pids/auth_service.pid)"; fi
  if [ -f .pids/org_service.pid ]; then kill "$(cat .pids/org_service.pid)"; fi
  if [ -f .pids/gateway.pid ]; then kill "$(cat .pids/gateway.pid)"; fi
  if [ -f .pids/audit_service.pid ]; then kill "$(cat .pids/audit_service.pid)"; fi
EOF
