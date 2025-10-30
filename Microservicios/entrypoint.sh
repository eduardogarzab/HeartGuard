#!/usr/bin/env sh
set -eu

PORT="${PORT:-${SERVICE_PORT:-5000}}"
# Run gunicorn from /app/service directory with app module
exec gunicorn --bind "0.0.0.0:${PORT}" app:app
