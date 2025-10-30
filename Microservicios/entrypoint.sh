#!/usr/bin/env sh
set -eu

PORT="${PORT:-${SERVICE_PORT:-5000}}"
exec gunicorn --bind "0.0.0.0:${PORT}" app:app
