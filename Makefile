# =========================
# HeartGuard Monorepo Makefile (DB + Backend)
# =========================

APP := superadmin-api

# Cargar y exportar variables desde .env si existe
ifneq (,$(wildcard .env))
include .env
export
endif

# --------- Guards ---------
ifndef DATABASE_URL
$(info [i] DATABASE_URL no está en el entorno. Asegúrate de tener .env en la raíz.)
endif

# Usado por psql (para init/seed con el superuser)
export PGPASSWORD := $(PGSUPER_PASS)

# DSN de app (para health/psql)
DB_URL := postgres://$(DBUSER):$(DBPASS)@$(PGHOST):$(PGPORT)/$(DBNAME)?sslmode=disable

# =========================
# Backend (Go)
# =========================
.PHONY: run dev build lint test tidy

run:
	@echo ">> running $(APP) (HTTP_ADDR=$(HTTP_ADDR))"
	GOFLAGS=-mod=mod \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) SUPERADMIN_TEST_TOKEN=$(SUPERADMIN_TEST_TOKEN) \
	go run ./cmd/$(APP)

dev:
	@echo ">> dev $(APP) (HTTP_ADDR=$(HTTP_ADDR))"
	GOFLAGS=-mod=mod \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) SUPERADMIN_TEST_TOKEN=$(SUPERADMIN_TEST_TOKEN) \
	go run ./cmd/$(APP)

build:
	@echo ">> build $(APP)"
	GOOS=linux GOARCH=amd64 go build -o bin/$(APP) ./cmd/$(APP)

lint:
	@echo ">> go vet"
	go vet ./...

test:
	@echo ">> go test"
	go test ./...

tidy:
	@echo ">> go mod tidy"
	cd backend 2>/dev/null || true
	go mod tidy

# =========================
# Docker (Postgres service)
# =========================
.PHONY: up down logs

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
# DB (init/seed/health)
# =========================
.PHONY: help perms db-url db-init db-seed db-reset db-drop db-health db-psql

help:
	@echo "Targets:"
	@echo "  make up/down/logs   -> docker postgres"
	@echo "  make dev/run        -> backend"
	@echo "  make tidy           -> go mod tidy"
	@echo "  make perms          -> fija permisos de scripts/sql"
	@echo "  make db-url         -> imprime el DSN app"
	@echo "  make db-init        -> crea rol, DB, schema, extensiones, DDL (init.sql)"
	@echo "  make db-seed        -> carga semillas (seed.sql)"
	@echo "  make db-reset       -> drop -> init -> seed"
	@echo "  make db-drop        -> dropdb (ignora error si no existe)"
	@echo "  make db-health      -> checks básicos contra DB"
	@echo "  make db-psql        -> psql como app user (DSN)"

perms:
	@chmod 644 db/*.sql 2>/dev/null || true
	@chmod 755 scripts/*.sh 2>/dev/null || true

db-url:
	@echo "$(DB_URL)"

db-init: perms
	@echo "== init.sql =="
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
