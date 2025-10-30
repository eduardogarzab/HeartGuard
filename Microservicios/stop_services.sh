#!/usr/bin/env bash
set -euo pipefail

export COMPOSE_PROJECT_NAME=heartguard_micro

docker compose --env-file .env down --remove-orphans
