# =============================================================================
# HeartGuard Services - Makefile Maestro
# =============================================================================
# Gestión centralizada de todos los microservicios (auth, admin, user, gateway)
# =============================================================================

SHELL := /bin/bash
SERVICES := auth admin user patient media gateway influxdb ai aimonitor
PYTHON := python3
VENV := .venv

# Puertos por defecto
AUTH_PORT := 5001
ADMIN_PORT := 5002
USER_PORT := 5003
PATIENT_PORT := 5004
MEDIA_PORT := 5005
GATEWAY_PORT := 8080
REALTIME_PORT := 5006
AI_PORT := 5007
AIMONITOR_PORT := 5008

# Directorio de logs
LOG_DIR := /tmp/heartguard-logs
PID_DIR := /tmp/heartguard-pids

.PHONY: help install start stop restart status logs clean test

# =============================================================================
# Ayuda
# =============================================================================
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  HeartGuard Services - Comandos Disponibles"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  📦 Instalación:"
	@echo "    make install              - Instalar dependencias de todos los servicios"
	@echo "    make install-auth         - Instalar solo auth-service"
	@echo "    make install-admin        - Instalar solo admin-service"
	@echo "    make install-user         - Instalar solo user-service"
	@echo "    make install-patient      - Instalar solo patient-service"
	@echo "    make install-media        - Instalar solo media-service"
	@echo "    make install-gateway      - Instalar solo gateway"
	@echo "    make install-influxdb     - Instalar solo influxdb-service"
	@echo "    make install-ai           - Instalar solo ai-prediction"
	@echo "    make install-aimonitor    - Instalar solo ai-monitor"
	@echo ""
	@echo "  🚀 Gestión de Servicios:"
	@echo "    make start                - Iniciar todos los servicios"
	@echo "    make start-auth           - Iniciar solo auth-service"
	@echo "    make start-admin          - Iniciar solo admin-service"
	@echo "    make start-user           - Iniciar solo user-service"
	@echo "    make start-patient        - Iniciar solo patient-service"
	@echo "    make start-media          - Iniciar solo media-service"
	@echo "    make start-gateway        - Iniciar solo gateway"
	@echo "    make start-influxdb       - Iniciar solo influxdb-service"
	@echo "    make start-ai             - Iniciar solo ai-prediction"
	@echo "    make start-aimonitor      - Iniciar solo ai-monitor"
	@echo ""
	@echo "  🔄 Control:"
	@echo "    make restart              - Reiniciar todos los servicios"
	@echo "    make restart-auth         - Reiniciar solo auth-service"
	@echo "    make restart-admin        - Reiniciar solo admin-service"
	@echo "    make restart-user         - Reiniciar solo user-service"
	@echo "    make restart-patient      - Reiniciar solo patient-service"
	@echo "    make restart-media        - Reiniciar solo media-service"
	@echo "    make restart-gateway      - Reiniciar solo gateway"
	@echo "    make restart-influxdb     - Reiniciar solo influxdb-service"
	@echo "    make restart-ai           - Reiniciar solo ai-prediction"
	@echo "    make restart-aimonitor    - Reiniciar solo ai-monitor"
	@echo ""
	@echo "  🛑 Detener:"
	@echo "    make stop                 - Detener todos los servicios"
	@echo "    make stop-auth            - Detener solo auth-service"
	@echo "    make stop-admin           - Detener solo admin-service"
	@echo "    make stop-user            - Detener solo user-service"
	@echo "    make stop-patient         - Detener solo patient-service"
	@echo "    make stop-media           - Detener solo media-service"
	@echo "    make stop-gateway         - Detener solo gateway"
	@echo "    make stop-influxdb        - Detener solo influxdb-service"
	@echo "    make stop-ai              - Detener solo ai-prediction"
	@echo "    make stop-aimonitor       - Detener solo ai-monitor"
	@echo ""
	@echo "  📊 Monitoreo:"
	@echo "    make status               - Ver estado de todos los servicios"
	@echo "    make logs                 - Ver logs de todos los servicios (últimas 50 líneas)"
	@echo "    make logs-auth            - Ver logs de auth-service"
	@echo "    make logs-admin           - Ver logs de admin-service"
	@echo "    make logs-user            - Ver logs de user-service"
	@echo "    make logs-patient         - Ver logs de patient-service"
	@echo "    make logs-media           - Ver logs de media-service"
	@echo "    make logs-gateway         - Ver logs de gateway"
	@echo "    make logs-influxdb        - Ver logs de influxdb-service"
	@echo "    make logs-ai              - Ver logs de ai-prediction"
	@echo "    make logs-aimonitor       - Ver logs de ai-monitor"
	@echo "    make tail                 - Seguir logs en tiempo real (todos)"
	@echo "    make tail-auth            - Seguir logs de auth-service"
	@echo "    make tail-admin           - Seguir logs de admin-service"
	@echo "    make tail-user            - Seguir logs de user-service"
	@echo "    make tail-patient         - Seguir logs de patient-service"
	@echo "    make tail-media           - Seguir logs de media-service"
	@echo "    make tail-gateway         - Seguir logs de gateway"
	@echo "    make tail-influxdb        - Seguir logs de influxdb-service"
	@echo "    make tail-ai              - Seguir logs de ai-prediction"
	@echo "    make tail-aimonitor       - Seguir logs de ai-monitor"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    make test                 - Ejecutar tests de todos los servicios"
	@echo "    make test-auth            - Ejecutar tests de auth-service"
	@echo "    make test-admin           - Ejecutar tests de admin-service"
	@echo "    make test-user            - Ejecutar tests de user-service"
	@echo "    make test-patient         - Ejecutar tests de patient-service"
	@echo "    make test-media           - Ejecutar tests de media-service"
	@echo "    make test-gateway         - Ejecutar tests de gateway"
	@echo "    make test-influxdb        - Ejecutar tests de influxdb-service"
	@echo "    make test-ai              - Ejecutar tests de ai-prediction"
	@echo "    make test-aimonitor       - Ejecutar tests de ai-monitor"
	@echo ""
	@echo "  🧹 Limpieza:"
	@echo "    make clean                - Limpiar caches y archivos temporales"
	@echo "    make clean-venv           - Eliminar entornos virtuales"
	@echo "    make clean-all            - Limpieza completa (incluye venv)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# =============================================================================
# Instalación
# =============================================================================
install: install-auth install-admin install-user install-patient install-media install-gateway install-influxdb install-ai install-aimonitor
	@echo "✓ Todas las dependencias instaladas"

install-auth:
	@echo "📦 Instalando auth-service..."
	@cd auth && $(MAKE) install

install-admin:
	@echo "📦 Instalando admin-service..."
	@cd admin && $(MAKE) install

install-user:
	@echo "📦 Instalando user-service..."
	@cd user && $(MAKE) install

install-patient:
	@echo "📦 Instalando patient-service..."
	@cd patient && $(MAKE) install

install-media:
	@echo "📦 Instalando media-service..."
	@cd media && $(MAKE) install

install-gateway:
	@echo "📦 Instalando gateway..."
	@cd gateway && $(MAKE) install

install-influxdb:
	@echo "📦 Instalando influxdb-service..."
	@cd influxdb-service && $(MAKE) install

install-ai:
	@echo "📦 Instalando ai-prediction..."
	@cd ai-prediction && $(MAKE) install

install-aimonitor:
	@echo "📦 Instalando ai-monitor..."
	@cd ai-monitor && $(MAKE) install

# =============================================================================
# Iniciar Servicios
# =============================================================================
$(LOG_DIR):
	@mkdir -p $(LOG_DIR)

$(PID_DIR):
	@mkdir -p $(PID_DIR)

start: $(LOG_DIR) $(PID_DIR) start-auth wait-auth start-admin wait-admin start-user wait-user start-patient wait-patient start-media wait-media start-gateway wait-gateway start-influxdb wait-influxdb start-ai wait-ai start-aimonitor wait-aimonitor
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  ✓ Todos los servicios iniciados correctamente"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(MAKE) --no-print-directory status

start-auth: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando auth-service en puerto $(AUTH_PORT)..."
	@cd auth && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=auth.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(AUTH_PORT) --no-reload \
			> $(LOG_DIR)/auth.log 2>&1 & \
		echo $$! > $(PID_DIR)/auth.pid
	@echo "  PID: $$(cat $(PID_DIR)/auth.pid)"

start-admin: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando admin-service en puerto $(ADMIN_PORT)..."
	@cd admin && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=admin.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(ADMIN_PORT) --no-reload \
			> $(LOG_DIR)/admin.log 2>&1 & \
		echo $$! > $(PID_DIR)/admin.pid
	@echo "  PID: $$(cat $(PID_DIR)/admin.pid)"

start-user: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando user-service en puerto $(USER_PORT)..."
	@cd user && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=src.user.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(USER_PORT) --no-reload \
			> $(LOG_DIR)/user.log 2>&1 & \
		echo $$! > $(PID_DIR)/user.pid
	@echo "  PID: $$(cat $(PID_DIR)/user.pid)"

start-patient: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando patient-service en puerto $(PATIENT_PORT)..."
	@cd patient && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=src.patient.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(PATIENT_PORT) --no-reload \
			> $(LOG_DIR)/patient.log 2>&1 & \
		echo $$! > $(PID_DIR)/patient.pid
	@echo "  PID: $$(cat $(PID_DIR)/patient.pid)"

start-media: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando media-service en puerto $(MEDIA_PORT)..."
	@cd media && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=media.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(MEDIA_PORT) --no-reload \
			> $(LOG_DIR)/media.log 2>&1 & \
		echo $$! > $(PID_DIR)/media.pid
	@echo "  PID: $$(cat $(PID_DIR)/media.pid)"

start-gateway: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando gateway en puerto $(GATEWAY_PORT)..."
	@cd gateway && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=gateway.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(GATEWAY_PORT) --no-reload \
			> $(LOG_DIR)/gateway.log 2>&1 & \
		echo $$! > $(PID_DIR)/gateway.pid
	@echo "  PID: $$(cat $(PID_DIR)/gateway.pid)"

start-influxdb: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando influxdb-service en puerto $(REALTIME_PORT)..."
	@cd influxdb-service && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=generator.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(REALTIME_PORT) --no-reload \
			> $(LOG_DIR)/realtime.log 2>&1 & \
		echo $$! > $(PID_DIR)/realtime.pid
	@echo "  PID: $$(cat $(PID_DIR)/realtime.pid)"

start-ai: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando ai-prediction en puerto $(AI_PORT)..."
	@cd ai-prediction && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=src.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(AI_PORT) --no-reload \
			> $(LOG_DIR)/ai.log 2>&1 & \
		echo $$! > $(PID_DIR)/ai.pid
	@echo "  PID: $$(cat $(PID_DIR)/ai.pid)"

start-aimonitor: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando ai-monitor en puerto $(AIMONITOR_PORT)..."
	@cd ai-monitor && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=src.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(AIMONITOR_PORT) --no-reload \
			> $(LOG_DIR)/aimonitor.log 2>&1 & \
		echo $$! > $(PID_DIR)/aimonitor.pid
	@echo "  PID: $$(cat $(PID_DIR)/aimonitor.pid)"

# Esperar a que los servicios estén listos
wait-auth:
	@echo "  ⏳ Esperando a que auth-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(AUTH_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ Auth-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando auth-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-admin:
	@echo "  ⏳ Esperando a que admin-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(ADMIN_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ Admin-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando admin-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-user:
	@echo "  ⏳ Esperando a que user-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(USER_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ User-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando user-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-patient:
	@echo "  ⏳ Esperando a que patient-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(PATIENT_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ Patient-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando patient-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-media:
	@echo "  ⏳ Esperando a que media-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(MEDIA_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ Media-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando media-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-gateway:
	@echo "  ⏳ Esperando a que gateway esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(GATEWAY_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ Gateway respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando gateway"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-influxdb:
	@echo "  ⏳ Esperando a que influxdb-service esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(REALTIME_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ InfluxDB-service respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando influxdb-service"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-ai:
	@echo "  ⏳ Esperando a que ai-prediction esté listo..."
	@for i in {1..30}; do \
		if curl -s http://localhost:$(AI_PORT)/health > /dev/null 2>&1; then \
			echo "  ✓ AI-prediction respondiendo"; \
			break; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "  ✗ Timeout esperando ai-prediction"; \
			exit 1; \
		fi; \
		sleep 1; \
	done

wait-aimonitor:
	@echo "  ⏳ Esperando a que ai-monitor esté listo..."
	@sleep 2
	@if [ -f $(PID_DIR)/aimonitor.pid ]; then \
		pid=$$(cat $(PID_DIR)/aimonitor.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			echo "  ✓ AI-monitor respondiendo"; \
		else \
			echo "  ✗ AI-monitor no inició correctamente"; \
			exit 1; \
		fi; \
	else \
		echo "  ✗ AI-monitor PID file not found"; \
		exit 1; \
	fi

# =============================================================================
# Detener Servicios
# =============================================================================
stop: stop-aimonitor stop-ai stop-influxdb stop-gateway stop-media stop-patient stop-user stop-admin stop-auth
	@echo "✓ Todos los servicios detenidos"

stop-auth:
	@if [ -f $(PID_DIR)/auth.pid ]; then \
		echo "🛑 Deteniendo auth-service (PID: $$(cat $(PID_DIR)/auth.pid))..."; \
		kill $$(cat $(PID_DIR)/auth.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/auth.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/auth.pid; \
	fi
	@lsof -ti :$(AUTH_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ Auth-service detenido"

stop-admin:
	@if [ -f $(PID_DIR)/admin.pid ]; then \
		echo "🛑 Deteniendo admin-service (PID: $$(cat $(PID_DIR)/admin.pid))..."; \
		kill $$(cat $(PID_DIR)/admin.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/admin.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/admin.pid; \
	fi
	@lsof -ti :$(ADMIN_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ Admin-service detenido"

stop-user:
	@if [ -f $(PID_DIR)/user.pid ]; then \
		echo "🛑 Deteniendo user-service (PID: $$(cat $(PID_DIR)/user.pid))..."; \
		kill $$(cat $(PID_DIR)/user.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/user.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/user.pid; \
	fi
	@lsof -ti :$(USER_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ User-service detenido"

stop-patient:
	@if [ -f $(PID_DIR)/patient.pid ]; then \
		echo "🛑 Deteniendo patient-service (PID: $$(cat $(PID_DIR)/patient.pid))..."; \
		kill $$(cat $(PID_DIR)/patient.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/patient.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/patient.pid; \
	fi
	@lsof -ti :$(PATIENT_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ Patient-service detenido"

stop-media:
	@if [ -f $(PID_DIR)/media.pid ]; then \
		echo "🛑 Deteniendo media-service (PID: $$(cat $(PID_DIR)/media.pid))..."; \
		kill $$(cat $(PID_DIR)/media.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/media.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/media.pid; \
	fi
	@lsof -ti :$(MEDIA_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ Media-service detenido"

stop-gateway:
	@if [ -f $(PID_DIR)/gateway.pid ]; then \
		echo "🛑 Deteniendo gateway (PID: $$(cat $(PID_DIR)/gateway.pid))..."; \
		kill $$(cat $(PID_DIR)/gateway.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/gateway.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/gateway.pid; \
	fi
	@lsof -ti :$(GATEWAY_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ Gateway detenido"

stop-influxdb:
	@if [ -f $(PID_DIR)/realtime.pid ]; then \
		echo "🛑 Deteniendo influxdb-service (PID: $$(cat $(PID_DIR)/realtime.pid))..."; \
		kill $$(cat $(PID_DIR)/realtime.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/realtime.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/realtime.pid; \
	fi
	@lsof -ti :$(REALTIME_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ InfluxDB-service detenido"

stop-ai:
	@if [ -f $(PID_DIR)/ai.pid ]; then \
		echo "🛑 Deteniendo ai-prediction (PID: $$(cat $(PID_DIR)/ai.pid))..."; \
		kill $$(cat $(PID_DIR)/ai.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/ai.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/ai.pid; \
	fi
	@lsof -ti :$(AI_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ AI-prediction detenido"

stop-aimonitor:
	@if [ -f $(PID_DIR)/aimonitor.pid ]; then \
		echo "🛑 Deteniendo ai-monitor (PID: $$(cat $(PID_DIR)/aimonitor.pid))..."; \
		kill $$(cat $(PID_DIR)/aimonitor.pid) 2>/dev/null || true; \
		sleep 1; \
		kill -9 $$(cat $(PID_DIR)/aimonitor.pid) 2>/dev/null || true; \
		rm -f $(PID_DIR)/aimonitor.pid; \
	fi
	@lsof -ti :$(AIMONITOR_PORT) | xargs kill -9 2>/dev/null || true
	@echo "  ✓ AI-monitor detenido"

# =============================================================================
# Reiniciar Servicios
# =============================================================================
restart: stop start

restart-auth: stop-auth start-auth wait-auth
	@echo "✓ Auth-service reiniciado"

restart-admin: stop-admin start-admin wait-admin
	@echo "✓ Admin-service reiniciado"

restart-user: stop-user start-user wait-user
	@echo "✓ User-service reiniciado"

restart-patient: stop-patient start-patient wait-patient
	@echo "✓ Patient-service reiniciado"

restart-media: stop-media start-media wait-media
	@echo "✓ Media-service reiniciado"

restart-gateway: stop-gateway start-gateway wait-gateway
	@echo "✓ Gateway reiniciado"

restart-influxdb: stop-influxdb start-influxdb wait-influxdb
	@echo "✓ InfluxDB-service reiniciado"

restart-ai: stop-ai start-ai wait-ai
	@echo "✓ AI-prediction reiniciado"

restart-aimonitor: stop-aimonitor start-aimonitor wait-aimonitor
	@echo "✓ AI-monitor reiniciado"

# =============================================================================
# Estado y Monitoreo
# =============================================================================
status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Estado de Servicios HeartGuard"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@printf "  %-20s %-10s %-10s %s\n" "Servicio" "Puerto" "Estado" "PID"
	@echo "  ────────────────────────────────────────────────────────────"
	@if [ -f $(PID_DIR)/auth.pid ]; then \
		pid=$$(cat $(PID_DIR)/auth.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "auth-service" "$(AUTH_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "auth-service" "$(AUTH_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "auth-service" "$(AUTH_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/admin.pid ]; then \
		pid=$$(cat $(PID_DIR)/admin.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "admin-service" "$(ADMIN_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "admin-service" "$(ADMIN_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "admin-service" "$(ADMIN_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/user.pid ]; then \
		pid=$$(cat $(PID_DIR)/user.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "user-service" "$(USER_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "user-service" "$(USER_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "user-service" "$(USER_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/patient.pid ]; then \
		pid=$$(cat $(PID_DIR)/patient.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "patient-service" "$(PATIENT_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "patient-service" "$(PATIENT_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "patient-service" "$(PATIENT_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/media.pid ]; then \
		pid=$$(cat $(PID_DIR)/media.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "media-service" "$(MEDIA_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "media-service" "$(MEDIA_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "media-service" "$(MEDIA_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/gateway.pid ]; then \
		pid=$$(cat $(PID_DIR)/gateway.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "gateway" "$(GATEWAY_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "gateway" "$(GATEWAY_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "gateway" "$(GATEWAY_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/realtime.pid ]; then \
		pid=$$(cat $(PID_DIR)/realtime.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "realtime-generator" "$(REALTIME_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "realtime-generator" "$(REALTIME_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "realtime-generator" "$(REALTIME_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/ai.pid ]; then \
		pid=$$(cat $(PID_DIR)/ai.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "ai-prediction" "$(AI_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "ai-prediction" "$(AI_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "ai-prediction" "$(AI_PORT)" "✗ Stopped" "-"; \
	fi
	@if [ -f $(PID_DIR)/aimonitor.pid ]; then \
		pid=$$(cat $(PID_DIR)/aimonitor.pid); \
		if ps -p $$pid > /dev/null 2>&1; then \
			printf "  %-20s %-10s %-10s %s\n" "ai-monitor" "$(AIMONITOR_PORT)" "✓ Running" "$$pid"; \
		else \
			printf "  %-20s %-10s %-10s %s\n" "ai-monitor" "$(AIMONITOR_PORT)" "✗ Stopped" "-"; \
		fi; \
	else \
		printf "  %-20s %-10s %-10s %s\n" "ai-monitor" "$(AIMONITOR_PORT)" "✗ Stopped" "-"; \
	fi
	@echo ""
	@echo "  Logs: $(LOG_DIR)/"
	@echo "  PIDs: $(PID_DIR)/"
	@echo ""

# =============================================================================
# Logs
# =============================================================================
logs:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - auth-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/auth.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - admin-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/admin.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - user-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/user.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - patient-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/patient.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - media-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/media.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - gateway"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/gateway.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - influxdb-service"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/realtime.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - ai-prediction"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/ai.log 2>/dev/null || echo "  (sin logs)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Logs - ai-monitor"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/aimonitor.log 2>/dev/null || echo "  (sin logs)"

logs-auth:
	@tail -n 100 $(LOG_DIR)/auth.log 2>/dev/null || echo "Sin logs de auth-service"

logs-admin:
	@tail -n 100 $(LOG_DIR)/admin.log 2>/dev/null || echo "Sin logs de admin-service"

logs-user:
	@tail -n 100 $(LOG_DIR)/user.log 2>/dev/null || echo "Sin logs de user-service"

logs-patient:
	@tail -n 100 $(LOG_DIR)/patient.log 2>/dev/null || echo "Sin logs de patient-service"

logs-media:
	@tail -n 100 $(LOG_DIR)/media.log 2>/dev/null || echo "Sin logs de media-service"

logs-gateway:
	@tail -n 100 $(LOG_DIR)/gateway.log 2>/dev/null || echo "Sin logs de gateway"

logs-influxdb:
	@tail -n 100 $(LOG_DIR)/realtime.log 2>/dev/null || echo "Sin logs de influxdb-service"

logs-ai:
	@tail -n 100 $(LOG_DIR)/ai.log 2>/dev/null || echo "Sin logs de ai-prediction"

logs-aimonitor:
	@tail -n 100 $(LOG_DIR)/aimonitor.log 2>/dev/null || echo "Sin logs de ai-monitor"

tail:
	@tail -f $(LOG_DIR)/*.log

tail-auth:
	@tail -f $(LOG_DIR)/auth.log

tail-admin:
	@tail -f $(LOG_DIR)/admin.log

tail-user:
	@tail -f $(LOG_DIR)/user.log

tail-patient:
	@tail -f $(LOG_DIR)/patient.log

tail-media:
	@tail -f $(LOG_DIR)/media.log

tail-gateway:
	@tail -f $(LOG_DIR)/gateway.log

tail-influxdb:
	@tail -f $(LOG_DIR)/realtime.log

tail-ai:
	@tail -f $(LOG_DIR)/ai.log

tail-aimonitor:
	@tail -f $(LOG_DIR)/aimonitor.log

# =============================================================================
# Testing
# =============================================================================
test: test-auth test-admin test-user test-patient test-media test-gateway test-influxdb test-ai test-aimonitor
	@echo "✓ Todos los tests completados"

test-auth:
	@echo "🧪 Ejecutando tests de auth-service..."
	@cd auth && ./test_auth_service.sh

test-admin:
	@echo "🧪 Ejecutando tests de admin-service..."
	@cd admin && ./test_admin_service.sh

test-user:
	@if [ -d user/tests ]; then \
		echo "🧪 Ejecutando tests de user-service..."; \
		cd user && $(MAKE) test; \
	else \
		echo "⚠️  user-service no tiene pruebas definidas"; \
	fi

test-patient:
	@if [ -d patient/tests ]; then \
		echo "🧪 Ejecutando tests de patient-service..."; \
		cd patient && $(MAKE) test; \
	else \
		echo "⚠️  patient-service no tiene pruebas definidas"; \
	fi

test-media:
	@if [ -d media/tests ]; then \
		echo "🧪 Ejecutando tests de media-service..."; \
		cd media && $(MAKE) test; \
	else \
		echo "⚠️  media-service no tiene pruebas definidas"; \
	fi

test-gateway:
	@echo "🧪 Ejecutando tests de gateway..."
	@cd gateway && ./test_gateway.sh

test-influxdb:
	@if [ -d influxdb-service/tests ]; then \
		echo "🧪 Ejecutando tests de influxdb-service..."; \
		cd influxdb-service && $(MAKE) test; \
	else \
		echo "⚠️  influxdb-service no tiene pruebas definidas"; \
	fi

test-ai:
	@if [ -d ai-prediction/tests ]; then \
		echo "🧪 Ejecutando tests de ai-prediction..."; \
		cd ai-prediction && $(MAKE) test; \
	else \
		echo "⚠️  ai-prediction no tiene pruebas definidas"; \
	fi

test-aimonitor:
	@if [ -d ai-monitor/tests ]; then \
		echo "🧪 Ejecutando tests de ai-monitor..."; \
		cd ai-monitor && $(MAKE) test; \
	else \
		echo "⚠️  ai-monitor no tiene pruebas definidas"; \
	fi

# =============================================================================
# Limpieza
# =============================================================================
clean:
	@echo "🧹 Limpiando caches y archivos temporales..."
	@for service in $(SERVICES); do \
		cd $$service && $(MAKE) clean && cd ..; \
	done
	@rm -rf $(LOG_DIR)
	@rm -rf $(PID_DIR)
	@echo "✓ Limpieza completada"

clean-venv:
	@echo "🧹 Eliminando entornos virtuales..."
	@for service in $(SERVICES); do \
		echo "  - $$service"; \
		rm -rf $$service/$(VENV); \
	done
	@echo "✓ Entornos virtuales eliminados"

clean-all: stop clean clean-venv
	@echo "✓ Limpieza completa finalizada"

# =============================================================================
# Desarrollo
# =============================================================================
dev:
	@echo "🔧 Modo desarrollo - iniciando servicios con reload..."
	@echo "⚠️  Usa Ctrl+C para detener todos los servicios"
	@trap 'make stop' EXIT; \
	$(MAKE) start && \
	$(MAKE) tail
