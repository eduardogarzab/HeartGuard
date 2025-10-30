# =========================
# HeartGuard Microservices Makefile
# =========================

# Cargar y exportar variables del entorno local
ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE := docker compose --env-file .env
PROJECT := heartguard_micro
MEDIA_SECRET := secrets/gcp-sa.json
PORTS := 5000 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5672 8086
SERVICES ?=
SERVICE ?=
CMD ?=

export COMPOSE_PROJECT_NAME := $(PROJECT)

.PHONY: help doctor up down restart start stop build pull logs logs-% ps clean deep-clean \
	shell exec free-ports free-port-% check-env ensure-secret check-tools

help:
	@echo "Targets:"
	@echo "  up / down / restart [SERVICES=...]"
	@echo "  build / pull / logs / ps"
	@echo "  shell SERVICE=svc | exec SERVICE=svc CMD=\"...\""
	@echo "  clean / deep-clean / free-ports"
	@echo "  doctor (valida .env, secretos y puertos)"

# =========================
# Docker Compose (Microservices stack)
# =========================
doctor: check-env ensure-secret check-tools free-ports

up: check-env ensure-secret
	@echo ">> docker compose up -d $(SERVICES)"
	$(COMPOSE) up -d $(SERVICES)

down: check-env
	@echo ">> docker compose down"
	$(COMPOSE) down

restart: check-env ensure-secret
	@echo ">> restart $(SERVICES)"
	$(MAKE) --no-print-directory stop SERVICES="$(SERVICES)"
	$(MAKE) --no-print-directory free-ports PORTS="$(PORTS)"
	$(MAKE) --no-print-directory start SERVICES="$(SERVICES)"

start: check-env
	@echo ">> docker compose start $(SERVICES)"
	$(COMPOSE) start $(SERVICES)

stop: check-env
	@echo ">> docker compose stop $(SERVICES)"
	$(COMPOSE) stop $(SERVICES)

build: check-env
	@echo ">> docker compose build $(SERVICES)"
	$(COMPOSE) build $(SERVICES)

pull: check-env
	@echo ">> docker compose pull $(SERVICES)"
	$(COMPOSE) pull $(SERVICES)

logs: check-env
	@echo ">> docker compose logs -f $(SERVICES)"
	$(COMPOSE) logs -f $(SERVICES)

logs-%: check-env
	@echo ">> docker compose logs -f $*"
	$(COMPOSE) logs -f $*

ps: check-env
	@echo ">> docker compose ps"
	$(COMPOSE) ps

clean: check-env
	@echo ">> docker compose down -v --remove-orphans"
	$(COMPOSE) down -v --remove-orphans

deep-clean: clean
	@echo ">> docker volume prune -f"
	docker volume prune -f

shell: check-env
	@if [ -z "$(SERVICE)" ]; then \
		echo "[ERROR] define SERVICE=<nombre>" >&2; \
		exit 1; \
	fi
	@echo ">> shell $(SERVICE)"
	$(COMPOSE) exec -it $(SERVICE) sh

exec: check-env
	@if [ -z "$(SERVICE)" ]; then \
		echo "[ERROR] define SERVICE=<nombre>" >&2; \
		exit 1; \
	fi
	@if [ -z "$(CMD)" ]; then \
		echo "[ERROR] define CMD=\"comando\"" >&2; \
		exit 1; \
	fi
	@echo ">> exec $(SERVICE): $(CMD)"
	$(COMPOSE) exec -T $(SERVICE) sh -lc "$(CMD)"

# =========================
# Helpers (env, secretos, puertos)
# =========================
check-tools:
	@if ! command -v fuser >/dev/null 2>&1 && ! command -v lsof >/dev/null 2>&1; then \
		echo "[WARN] instala 'fuser' o 'lsof' para liberar puertos automáticamente." >&2; \
	fi

check-env:
	@if [ ! -f .env ]; then \
		echo "[ERROR] .env no existe. Copia .env.example y configura credenciales." >&2; \
		exit 1; \
	fi

ensure-secret:
	@if [ ! -f $(MEDIA_SECRET) ]; then \
		echo "[WARN] $(MEDIA_SECRET) ausente; media_service fallará al iniciar." >&2; \
	fi

free-ports:
	@set -e; \
	for port in $(PORTS); do \
		$(MAKE) --no-print-directory free-port-$$port; \
	done

free-port-%:
	@port=$*; \
	if command -v fuser >/dev/null 2>&1; then \
		if fuser -n tcp $$port >/dev/null 2>&1; then \
			echo ">> Liberando puerto $$port con fuser"; \
			fuser -n tcp -k $$port >/dev/null 2>&1 || true; \
			sleep 1; \
		else \
			echo ">> Puerto $$port libre"; \
		fi; \
	elif command -v lsof >/dev/null 2>&1; then \
		pids=$$(lsof -t -i :$$port 2>/dev/null | tr '\n' ' '); \
		if [ -n "$$pids" ]; then \
			echo ">> Liberando puerto $$port (PIDs: $$pids)"; \
			for pid in $$pids; do \
				kill $$pid 2>/dev/null || true; \
			done; \
			sleep 1; \
		else \
			echo ">> Puerto $$port libre"; \
		fi; \
	else \
		echo "[WARN] No se puede liberar puerto $$port automáticamente." >&2; \
	fi
