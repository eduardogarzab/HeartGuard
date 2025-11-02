# =========================
# HeartGuard Microservices Makefile
# =========================

# Cargar y exportar variables del entorno local
ifneq (,$(wildcard .env))
include .env
export
endif

# Variables para producción
ENV ?= development
ifeq ($(ENV),production)
	ENV_FILE := .env.production
	COMPOSE := docker compose --env-file .env.production
else
	ENV_FILE := .env
	COMPOSE := docker compose --env-file .env
endif

PROJECT := heartguard_micro
MEDIA_SECRET := secrets/gcp-sa.json
PORTS := 5000 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5672 8086
SERVICES ?=
SERVICE ?=
CMD ?=

export COMPOSE_PROJECT_NAME := $(PROJECT)

.PHONY: help doctor up down reset-all-microservices start stop build pull logs logs-% ps clean deep-clean \
	shell exec free-ports free-port-% check-env ensure-secret check-tools \
	prod-up prod-down prod-build prod-logs prod-ps prod-reset

help:
	@echo "Targets:"
	@echo "  Development:"
	@echo "    up / down / reset-all-microservices"
	@echo "    build / pull / logs / ps"
	@echo "    shell SERVICE=svc | exec SERVICE=svc CMD=\"...\""
	@echo "    clean / deep-clean / free-ports"
	@echo "  Production:"
	@echo "    prod-up / prod-down / prod-build / prod-logs / prod-ps / prod-reset"
	@echo "  Other:"
	@echo "    doctor (valida .env, secretos y puertos)"

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

reset-all-microservices: check-env
	@echo ">> RESET COMPLETO: Eliminando contenedores, imágenes y volúmenes del stack actual..."
	$(COMPOSE) down --rmi all -v
	@echo ">> Esperando a que Docker libere recursos de red..."
	sleep 3
	@echo ">> Eliminando contenedores huérfanos del proyecto actual..."
	docker ps -a --filter "name=$(PROJECT)" --format "{{.ID}}" | xargs -r docker rm -f
	@echo ">> Buscando y eliminando contenedores RabbitMQ residuales..."
	@docker ps -a --filter "ancestor=rabbitmq:3.12-management-alpine" --format "{{.ID}}\t{{.Names}}" | while read id name; do \
		if [ -n "$$id" ]; then \
			echo ">> Deteniendo y eliminando RabbitMQ residual: $$name"; \
			docker rm -f $$id >/dev/null 2>&1 || true; \
		fi; \
	done
	@echo ">> Limpiando sistema Docker (solo contenedores detenidos e imágenes huérfanas)..."
	docker system prune -a --volumes -f
	@echo ">> Forzando liberación de puertos usados por microservicios..."
	for p in $(PORTS); do \
		if sudo lsof -t -i :$$p >/dev/null 2>&1; then \
			echo "   - Cerrando puerto $$p (docker-proxy residual)"; \
			sudo lsof -t -i :$$p | xargs -r sudo kill -9 || true; \
		fi; \
	done
	sleep 2
	@echo ">> Reconstruyendo y levantando servicios..."
	$(MAKE) --no-print-directory ensure-secret
	$(COMPOSE) up -d --build


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

# =========================
# Production targets
# =========================
prod-up: ENV=production
prod-up:
	@echo ">> Levantando servicios en PRODUCCIÓN..."
	@if [ ! -f .env.production ]; then \
		echo "[ERROR] .env.production no existe" >&2; \
		exit 1; \
	fi
	docker compose --env-file .env.production -f docker-compose.prod.yml up -d $(SERVICES)

prod-down: ENV=production
prod-down:
	@echo ">> Deteniendo servicios de PRODUCCIÓN..."
	docker compose --env-file .env.production -f docker-compose.prod.yml down

prod-build: ENV=production
prod-build:
	@echo ">> Construyendo servicios de PRODUCCIÓN..."
	docker compose --env-file .env.production -f docker-compose.prod.yml build $(SERVICES)

prod-logs: ENV=production
prod-logs:
	@echo ">> Logs de servicios de PRODUCCIÓN..."
	docker compose --env-file .env.production -f docker-compose.prod.yml logs -f $(SERVICES)

prod-ps: ENV=production
prod-ps:
	@echo ">> Estado de servicios de PRODUCCIÓN..."
	docker compose --env-file .env.production -f docker-compose.prod.yml ps

prod-reset: ENV=production
prod-reset:
	@echo ">> RESET COMPLETO DE PRODUCCIÓN..."
	docker compose --env-file .env.production -f docker-compose.prod.yml down --rmi all -v
	@echo ">> Limpiando contenedores huérfanos..."
	docker ps -a --filter "name=$(PROJECT)" --format "{{.ID}}" | xargs -r docker rm -f
	docker system prune -a --volumes -f
	@echo ">> Reconstruyendo servicios..."
	docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
