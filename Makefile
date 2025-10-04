# =========================
# HeartGuard Makefile (DB + Backend)
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

.PHONY: help up down logs compose-wait db-wait \
        dev run build tidy lint test \
        db-url db-init db-seed db-reset db-drop db-health db-psql \
        reset-all

help:
	@echo "Targets:"
	@echo "  up / down / logs"
	@echo "  dev / run / build / tidy / lint / test (backend dentro de ./backend)"
	@echo "  db-init / db-seed / db-health / db-reset / db-psql"
	@echo "  reset-all (baja servicios, recrea volúmenes, espera y re-inicializa DB)"

# =========================
# Docker (Compose services)
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

# Opcionales: logs de Redis o ambos
logs-redis:
	@echo ">> docker compose logs -f redis"
	docker compose logs -f redis

logs-all:
	@echo ">> docker compose logs -f"
	docker compose logs -f

# Espera a Postgres: usa 'docker compose wait' si está disponible;
# si no, fallback con pg_isready dentro del contenedor.
WAIT_TIMEOUT ?= 60
WAIT_REDIS ?= 1

compose-wait:
	@set -e; \
	echo ">> Esperando a Postgres (timeout $(WAIT_TIMEOUT)s)..."; \
	for i in $$(seq 1 $(WAIT_TIMEOUT)); do \
	  if docker compose exec -T postgres pg_isready -U "$(PGSUPER)" -d postgres >/dev/null 2>&1; then \
	    echo "   Postgres listo"; \
	    break; \
	  fi; \
	  if [ $$i -eq $(WAIT_TIMEOUT) ]; then \
	    echo "!! Postgres no quedó listo a tiempo"; \
	    exit 1; \
	  fi; \
	  sleep 1; \
	done; \
	if [ "$(WAIT_REDIS)" = "1" ]; then \
	  echo ">> Esperando a Redis (timeout $(WAIT_TIMEOUT)s)..."; \
	  for j in $$(seq 1 $(WAIT_TIMEOUT)); do \
	    if docker compose exec -T redis sh -lc 'redis-cli PING >/dev/null 2>&1'; then \
	      echo "   Redis listo"; \
	      break; \
	    fi; \
	    if [ $$j -eq $(WAIT_TIMEOUT) ]; then \
	      echo "!! Redis no quedó listo a tiempo"; \
	      exit 1; \
	    fi; \
	    sleep 1; \
	  done; \
	else \
	  echo ">> Saltando espera de Redis (WAIT_REDIS=$(WAIT_REDIS))"; \
	fi

db-wait:
	@set -e; \
	printf ">> Verificando Postgres tras reinicio (timeout %ss)...\n" "$(WAIT_TIMEOUT)"; \
	ok=0; \
	for i in $$(seq 1 $(WAIT_TIMEOUT)); do \
	  if psql -U "$(PGSUPER)" -h "$(PGHOST)" -p "$(PGPORT)" -d postgres -c "SELECT 1;" >/dev/null 2>&1; then \
	    echo "   Postgres aceptando conexiones"; \
	    ok=1; \
	    break; \
	  fi; \
	  sleep 1; \
	done; \
	if [ $$ok -ne 1 ]; then \
	  echo "!! Postgres no respondió a tiempo tras el reinicio"; \
	  exit 1; \
	fi

# =========================
# Backend (Go) - ejecuta SIEMPRE dentro de ./backend
# =========================
dev:
	@echo ">> dev $(APP) (HTTP_ADDR=$(HTTP_ADDR))"
	cd backend && \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) \
	JWT_SECRET=$(JWT_SECRET) ACCESS_TOKEN_TTL=$(ACCESS_TOKEN_TTL) REFRESH_TOKEN_TTL=$(REFRESH_TOKEN_TTL) \
	REDIS_URL=$(REDIS_URL) RATE_LIMIT_RPS=$(RATE_LIMIT_RPS) RATE_LIMIT_BURST=$(RATE_LIMIT_BURST) \
	go run ./cmd/$(APP)

run:
	@echo ">> run $(APP)"
	cd backend && \
	ENV=$(ENV) HTTP_ADDR=$(HTTP_ADDR) DATABASE_URL=$(DATABASE_URL) \
	JWT_SECRET=$(JWT_SECRET) ACCESS_TOKEN_TTL=$(ACCESS_TOKEN_TTL) REFRESH_TOKEN_TTL=$(REFRESH_TOKEN_TTL) \
	REDIS_URL=$(REDIS_URL) RATE_LIMIT_RPS=$(RATE_LIMIT_RPS) RATE_LIMIT_BURST=$(RATE_LIMIT_BURST) \
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
	psql -v ON_ERROR_STOP=1 \
	     -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) \
	     -v dbname=$(DBNAME) -v dbuser=$(DBUSER) -v dbpass='$(DBPASS)' \
	     -f - < db/init.sql

db-seed:
	@echo "== seed.sql =="
	psql -v ON_ERROR_STOP=1 \
	     -U $(PGSUPER) -h $(PGHOST) -p $(PGPORT) -d $(DBNAME) \
	     -f - < db/seed.sql

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

# =========================
# Reset completo (Postgres + Redis + volúmenes)
# =========================
reset-all:
	@echo ">> Bajando servicios..."
	docker compose down -v --remove-orphans

	@echo ">> Borrando volúmenes (Postgres)..."
	- docker volume rm heartguard_postgres_data 2>/dev/null || true

	@echo ">> Levantando servicios limpios..."
	docker compose up -d

	@echo ">> Esperando a Postgres..."
	@$(MAKE) --no-print-directory compose-wait
	@$(MAKE) --no-print-directory db-wait

	@echo ">> Re-inicializando DB..."
	@$(MAKE) --no-print-directory db-init
	@$(MAKE) --no-print-directory db-seed

	@echo ">> Reset completo OK"
