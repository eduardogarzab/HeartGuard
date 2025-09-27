# =========================
# HeartGuard Monorepo Makefile (DB + Backend)
# =========================

APP := superadmin-api

# Cargar y exportar variables desde .env si existe
ifneq (,$(wildcard .env))
include .env
export
endif

# Usado por psql (para init/seed con el superuser)
export PGPASSWORD := $(PGSUPER_PASS)

# DSN de app (para health/psql)
DB_URL := postgres://$(DBUSER):$(DBPASS)@$(PGHOST):$(PGPORT)/$(DBNAME)?sslmode=disable

.PHONY: help up down logs \
        dev run build tidy lint test \
        db-url db-init db-seed db-reset db-drop db-health db-psql

help:
	@echo "Targets:"
	@echo "  up / down / logs"
	@echo "  dev / run / build / tidy / lint / test (backend dentro de ./backend)"
	@echo "  db-init / db-seed / db-health / db-reset / db-psql"

# =========================
# Docker (Postgres service)
# =========================
up:
	@echo ">> docker compose up -d"
	docker compose up -d

down:
	@echo ">> docker compose down"
	docker compose down

logs:
	@echo ">> docker compose logs -f postgres"
	docker compose logs -f postgres

# =========================
# Backend (Go) - ejecuta SIEMPRE dentro de ./backend
# =========================
dev:
	@echo ">> dev $(APP) (HTTP_ADDR=$(HTTP_ADDR))"
	cd backend && \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) SUPERADMIN_TEST_TOKEN=$(SUPERADMIN_TEST_TOKEN) \
	go run ./cmd/$(APP)

run:
	@echo ">> run $(APP)"
	cd backend && \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) SUPERADMIN_TEST_TOKEN=$(SUPERADMIN_TEST_TOKEN) \
	go run ./cmd/$(APP)

build:
	@echo ">> build $(APP)"
	cd backend && GOOS=linux GOARCH=amd64 go build -o bin/$(APP) ./cmd/$(APP)

tidy:
	@echo ">> go mod tidy"
	cd backend && go mod tidy

lint:
	@echo ">> go vet"
	cd backend && go vet ./...

test:
	@echo ">> go test"
	cd backend && go test ./...

# =========================
# DB (init/seed/health)
# =========================
db-url:
	@echo "$(DB_URL)"

db-init:
	@echo "== init.sql =="
	psql -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) -v dbname=$(DBNAME) -v dbuser=$(DBUSER) -v dbpass='$(DBPASS)' -f - < db/init.sql

db-seed:
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
