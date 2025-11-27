#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

bold() { printf '\033[1m%s\033[0m' "$1"; }

prompt() {
  local var_name=$1
  local label=$2
  local default=${3-}
  local secret=${4:-false}
  local value=""
  if [[ $secret == true ]]; then
    read -r -s -p "${label} [oculto]: " value || true
    printf '\n'
  else
    if [[ -n $default ]]; then
      read -r -p "${label} [${default}]: " value || true
    else
      read -r -p "${label}: " value || true
    fi
  fi
  if [[ -z $value && -n $default ]]; then
    value=$default
  fi
  printf -v "$var_name" '%s' "$value"
}

write_env() {
  local relative=$1
  shift
  local content=$*
  local path="$ROOT_DIR/${relative}"
  mkdir -p "$(dirname "$path")"
  cat > "$path" <<EOF
${content}
EOF
  printf '  • %s\n' "${relative}"
}

section() { printf '\n%s\n' "$(bold "$1")"; }

main() {
  section "Configuración general"
  prompt BACKEND_VM_IP "IP/hostname del backend" "134.199.204.58"
  prompt MICROSERVICES_VM_IP "IP/hostname de microservicios" "129.212.181.53"

  section "PostgreSQL"
  prompt PGSUPER "Usuario superadmin" "postgres"
  prompt PGSUPER_PASS "Password superadmin" "postgres123" true
  prompt PGPORT "Puerto expuesto" "5432"
  prompt DBNAME "Nombre de la base" "heartguard"
  prompt DBUSER "Usuario app" "heartguard_app"
  prompt DBPASS "Password app" "dev_change_me" true

  section "Redis / Influx"
  prompt REDIS_PORT "Puerto Redis" "6379"
  prompt INFLUXDB_PORT "Puerto Influx" "8086"
  prompt INFLUXDB_USERNAME "Usuario Influx" "admin"
  prompt INFLUXDB_PASSWORD "Password Influx" "influxdb123" true
  prompt INFLUXDB_BUCKET "Bucket" "timeseries"
  prompt INFLUXDB_ORG "Organización" "heartguard"
  prompt INFLUXDB_TOKEN "Token" "heartguard-dev-token-change-me" true

  section "Claves compartidas"
  prompt JWT_SECRET "JWT_SECRET" "dev_jwt_secret_change_me" true
  prompt INTERNAL_SERVICE_KEY "INTERNAL_SERVICE_KEY" "dev_internal_key" true
  prompt AI_MODEL_ID "AI_MODEL_ID" "988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc"

  section "DigitalOcean Spaces"
  prompt DO_SPACES_ID "Spaces Access Key" "DO00EXAMPLEID"
  prompt DO_SPACES_KEY "Spaces Secret Key" "DO00EXAMPLESECRET" true
  prompt DO_ORIGIN "Origin endpoint" "https://heartguard-bucket.atl1.digitaloceanspaces.com/"

  section "Gateway"
  prompt GATEWAY_SECRET "FLASK_SECRET_KEY" "change-me-in-production" true

  local DB_URL_HOST="postgres://${DBUSER}:${DBPASS}@${BACKEND_VM_IP}:${PGPORT}/${DBNAME}?sslmode=disable"
  local DB_URL_INTERNAL="postgres://${DBUSER}:${DBPASS}@postgres:5432/${DBNAME}?sslmode=disable"
  local REDIS_URL_HOST="redis://${BACKEND_VM_IP}:${REDIS_PORT}/0"
  local REDIS_URL_INTERNAL="redis://redis:6379/0"
  local INFLUX_URL_HOST="http://${BACKEND_VM_IP}:${INFLUXDB_PORT}"

  section "Escribiendo archivos .env"

  write_env ".env" "# Autogenerado por scripts/bootstrap-envs.sh
PGSUPER=${PGSUPER}
PGSUPER_PASS=${PGSUPER_PASS}
PGHOST=${BACKEND_VM_IP}
PGPORT=${PGPORT}
DBNAME=${DBNAME}
DBUSER=${DBUSER}
DBPASS=${DBPASS}
DATABASE_URL=${DB_URL_HOST}
BACKEND_VM_IP=${BACKEND_VM_IP}
MICROSERVICES_VM_IP=${MICROSERVICES_VM_IP}
ENV=prod
HTTP_ADDR=:8080
SECURE_COOKIES=true
JWT_SECRET=${JWT_SECRET}
ACCESS_TOKEN_TTL=15m
REFRESH_TOKEN_TTL=720h
REDIS_URL=${REDIS_URL_HOST}
RATE_LIMIT_RPS=10
RATE_LIMIT_BURST=20
INFLUXDB_URL=${INFLUX_URL_HOST}
INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
INFLUXDB_ORG=${INFLUXDB_ORG}
INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
"

  write_env "backend/.env" "ENV=prod
HTTP_ADDR=:8080
DATABASE_URL=${DB_URL_INTERNAL}
JWT_SECRET=${JWT_SECRET}
ACCESS_TOKEN_TTL=15m
REFRESH_TOKEN_TTL=720h
REDIS_URL=${REDIS_URL_INTERNAL}
RATE_LIMIT_RPS=10
RATE_LIMIT_BURST=20
SECURE_COOKIES=true
"

  write_env "micro-services/auth/.env" "DATABASE_URL=${DB_URL_HOST}
JWT_SECRET=${JWT_SECRET}
JWT_ACCESS_TOKEN_EXPIRES_MIN=15
JWT_REFRESH_TOKEN_EXPIRES_MIN=10080
BCRYPT_ROUNDS=12
LOG_LEVEL=INFO
SKIP_DB_INIT=0
"

  write_env "micro-services/admin/.env" "DATABASE_URL=${DB_URL_HOST}
AUTH_SERVICE_URL=http://auth-service:5001
FLASK_ENV=production
ADMIN_DEBUG=0
ADMIN_SERVICE_TIMEOUT=5
"

  write_env "micro-services/user/.env" "DATABASE_URL=${DB_URL_HOST}
JWT_SECRET=${JWT_SECRET}
PORT=5003
HOST=0.0.0.0
FLASK_ENV=production
CORS_ORIGINS=*
LOG_LEVEL=INFO
"

  write_env "micro-services/patient/.env" "DATABASE_URL=${DB_URL_HOST}
JWT_SECRET=${JWT_SECRET}
PORT=5004
HOST=0.0.0.0
FLASK_ENV=production
CORS_ORIGINS=*
LOG_LEVEL=INFO
"

  write_env "micro-services/media/.env" "ID=${DO_SPACES_ID}
KEY=${DO_SPACES_KEY}
ORIGIN_ENDPOINT=${DO_ORIGIN}
JWT_SECRET=${JWT_SECRET}
DATABASE_URL=${DB_URL_HOST}
MEDIA_MAX_FILE_MB=5
MEDIA_ALLOWED_CONTENT_TYPES=image/jpeg,image/png,image/webp
"

  write_env "micro-services/gateway/.env" "FLASK_DEBUG=0
FLASK_SECRET_KEY=${GATEWAY_SECRET}
GATEWAY_SERVICE_TIMEOUT=10
INTERNAL_SERVICE_KEY=${INTERNAL_SERVICE_KEY}
AUTH_SERVICE_URL=http://auth-service:5001
ADMIN_SERVICE_URL=http://admin-service:5002
USER_SERVICE_URL=http://user-service:5003
PATIENT_SERVICE_URL=http://patient-service:5004
MEDIA_SERVICE_URL=http://media-service:5005
REALTIME_SERVICE_URL=http://realtime-service:5006
AI_SERVICE_URL=http://ai-prediction:5007
"

  write_env "micro-services/influxdb-service/.env" "DATABASE_URL=${DB_URL_HOST}
INFLUXDB_URL=${INFLUX_URL_HOST}
INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
INFLUXDB_ORG=${INFLUXDB_ORG}
INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
GENERATION_INTERVAL=5
FLASK_DEBUG=0
"

  write_env "micro-services/ai-prediction/.env" "FLASK_HOST=0.0.0.0
FLASK_PORT=5007
FLASK_DEBUG=0
PREDICTION_THRESHOLD=0.6
JWT_SECRET=${JWT_SECRET}
INTERNAL_SERVICE_KEY=${INTERNAL_SERVICE_KEY}
"

  write_env "micro-services/ai-monitor/.env" "INFLUXDB_URL=${INFLUX_URL_HOST}
INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
INFLUXDB_ORG=${INFLUXDB_ORG}
INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
POSTGRES_HOST=${BACKEND_VM_IP}
POSTGRES_PORT=${PGPORT}
POSTGRES_DB=${DBNAME}
POSTGRES_USER=${DBUSER}
POSTGRES_PASSWORD=${DBPASS}
AI_SERVICE_URL=http://ai-prediction:5007
AI_PREDICTION_THRESHOLD=0.6
AI_MODEL_ID=${AI_MODEL_ID}
INTERNAL_SERVICE_KEY=${INTERNAL_SERVICE_KEY}
MONITOR_INTERVAL=60
LOOKBACK_WINDOW=300
BATCH_SIZE=10
FLASK_HOST=0.0.0.0
FLASK_PORT=5008
FLASK_DEBUG=false
LOG_LEVEL=INFO
ENABLE_NOTIFICATIONS=true
"

  printf '\n%s\n' "$(bold "Listo: revisa los archivos antes de levantar los contenedores.")"
  printf 'Backend: docker compose up -d\n'
  printf 'Microservicios: (cd docker/microservices && docker compose up -d)\n'
}

main "$@"
