#!/usr/bin/env bash
set -euo pipefail

if [ -f ".env" ]; then
  set -a; source .env; set +a
fi

DBNAME="${DBNAME:-heartguard}"
DBUSER="${DBUSER:-heartguard_app}"
DBPASS="${DBPASS:-dev_change_me}"
PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"

DB_URL="postgres://${DBUSER}:${DBPASS}@${PGHOST}:${PGPORT}/${DBNAME}?sslmode=disable"

echo "== Health check @ ${DB_URL} =="
psql "$DB_URL" -c "SELECT 1 AS ping;"
psql "$DB_URL" -c "SHOW search_path;"
psql "$DB_URL" -c "SELECT postgis_version();"
psql "$DB_URL" -c "SELECT count(*) AS roles FROM roles;"
psql "$DB_URL" -c "SELECT count(*) AS permissions FROM permissions;"
psql "$DB_URL" -c "SELECT count(*) AS statuses FROM user_statuses;"
psql "$DB_URL" -c "SELECT count(*) AS alert_levels FROM alert_levels;"
psql "$DB_URL" -c "SELECT email FROM users WHERE email='admin@heartguard.com';"
echo "[✓] OK"
