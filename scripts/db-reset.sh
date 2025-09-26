#!/usr/bin/env bash
set -euo pipefail

# Carga .env si existe
if [ -f ".env" ]; then
  set -a; source .env; set +a
fi

export PGPASSWORD="${PGSUPER_PASS:-}"
PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
PGSUPER="${PGSUPER:-postgres}"
DBNAME="${DBNAME:-heartguard}"
DBUSER="${DBUSER:-heartguard_app}"
DBPASS="${DBPASS:-dev_change_me}"

echo "[*] Dropping database $DBNAME (si existe)..."
dropdb -U "$PGSUPER" -h "$PGHOST" -p "$PGPORT" "$DBNAME" || true

echo "[*] Running init.sql..."
psql -U "$PGSUPER" -h "$PGHOST" -p "$PGPORT" \
  -v dbname="$DBNAME" -v dbuser="$DBUSER" -v dbpass="$DBPASS" \
  -f - < db/init.sql

echo "[*] Running seed.sql..."
psql -U "$PGSUPER" -h "$PGHOST" -p "$PGPORT" -d "$DBNAME" -f - < db/seed.sql

echo "[✓] Done."
