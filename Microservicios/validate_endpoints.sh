#!/usr/bin/env bash
set -euo pipefail
if [ $# -lt 1 ]; then
  echo "Usage: $0 <host>"
  exit 1
fi
HOST=$1
SERVICES=("gateway:5000" "auth:5001" "organization:5002" "user:5003" "media:5004" "timeseries:5005" "audit:5006")
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

echo "=============================================="
echo "Validating Heartguard endpoints on $HOST"
echo "=============================================="
for svc in "${SERVICES[@]}"; do
  name=${svc%%:*}
  port=${svc##*:}
  for accept in "application/json" "application/xml"; do
    start=$(date +%s%3N)
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "Accept: $accept" "http://$HOST:$port/health")
    end=$(date +%s%3N)
    body=${response%%HTTPSTATUS:*}
    status=${response##*HTTPSTATUS:}
    latency=$((end - start))
    if [ "$status" = "200" ]; then
      result="OK"
    else
      result="FAIL"
    fi
    echo "[$name][$accept] code=$status latency_ms=$latency status=$result"
    echo "$body"
    echo "----------------------------------------------"
  done
  echo
  echo "=============================================="
done
