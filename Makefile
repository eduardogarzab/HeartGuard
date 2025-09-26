# =========================
# HeartGuard DB Makefile
# =========================

include .env
export PGPASSWORD := $(PGSUPER_PASS)

DB_URL := postgres://$(DBUSER):$(DBPASS)@$(PGHOST):$(PGPORT)/$(DBNAME)?sslmode=disable

.PHONY: help db-url db-init db-seed db-reset db-drop db-health db-psql perms

help:
	@echo "Targets:"
	@echo "  make perms         -> fija permisos de archivos (644/755)"
	@echo "  make db-url        -> imprime el DSN app"
	@echo "  make db-init       -> crea rol, DB, schema, extensiones, DDL (init.sql)"
	@echo "  make db-seed       -> carga semillas (seed.sql)"
	@echo "  make db-reset      -> drop -> init -> seed"
	@echo "  make db-drop       -> dropdb (ignora error si no existe)"
	@echo "  make db-health     -> checks básicos"
	@echo "  make db-psql       -> psql como app user (DSN)"

perms:
	chmod 644 db/*.sql || true
	chmod 755 scripts/*.sh || true

db-url:
	@echo "$(DB_URL)"

db-init: perms
	@echo "== init.sql =="
	# Importa por stdin (-f -) para evitar problemas de lectura de archivos
	psql -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) -v dbname=$(DBNAME) -v dbuser=$(DBUSER) -v dbpass='$(DBPASS)' -f - < db/init.sql

db-seed: perms
	@echo "== seed.sql =="
	psql -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) -d $(DBNAME) -f - < db/seed.sql

db-reset: db-drop db-init db-seed

db-drop:
	- dropdb -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) $(DBNAME)

db-health:
	@echo "== Health check ==" && \
	psql "$(DB_URL)" -c "SELECT 1 AS ping;" && \
	psql "$(DB_URL)" -c "SHOW search_path;" && \
	psql "$(DB_URL)" -c "SELECT postgis_version();" && \
	psql "$(DB_URL)" -c "SELECT count(*) AS roles FROM roles;" && \
	psql "$(DB_URL)" -c "SELECT count(*) AS permissions FROM permissions;" && \
	psql "$(DB_URL)" -c "SELECT count(*) AS statuses FROM user_statuses;" && \
	psql "$(DB_URL)" -c "SELECT count(*) AS alert_levels FROM alert_levels;" && \
	psql "$(DB_URL)" -c "SELECT email FROM users WHERE email='admin@heartguard.com';"

db-psql:
	psql "$(DB_URL)"
