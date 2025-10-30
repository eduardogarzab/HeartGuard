#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

echo "[Heartguard] Starting services with docker-compose..."
docker-compose up -d

echo "[Heartguard] Current containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
