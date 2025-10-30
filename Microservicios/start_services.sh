#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "[ERROR] .env file not found in $(pwd)/Microservicios" >&2
  echo "Copy .env.example to .env and configure real values." >&2
  exit 1
fi

if [[ ! -f secrets/gcp-sa.json ]]; then
  echo "[WARN] secrets/gcp-sa.json not found. Media service will fail to start." >&2
fi

export COMPOSE_PROJECT_NAME=heartguard_micro

docker compose --env-file .env pull

docker compose --env-file .env up -d --build

docker compose --env-file .env ps
