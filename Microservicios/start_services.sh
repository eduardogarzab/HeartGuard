#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
  echo "[ERROR] Archivo .env no encontrado. Copie .env.example a .env y configure las variables." >&2
  exit 1
fi

echo "[INFO] Construyendo y levantando servicios..."
docker-compose --env-file .env up -d --build

# Esperar health básico del gateway
TRIES=30
for i in $(seq 1 $TRIES); do
  STATUS=$(curl -sk -o /dev/null -w "%{http_code}" http://localhost:5000/gateway/health || true)
  if [[ "$STATUS" == "200" ]]; then
    echo "[INFO] Gateway saludable."
    exit 0
  fi
  echo "[INFO] Esperando gateway... ($i/$TRIES)"
  sleep 2
done

echo "[WARN] No se pudo verificar la salud del gateway tras $TRIES intentos. Revise logs con docker-compose logs."
exit 1
