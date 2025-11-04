# =============================================================================
# HeartGuard Services - Makefile Maestro
# =============================================================================
# Gestión centralizada de todos los microservicios (auth, admin, gateway)
# =============================================================================

SHELL := /bin/bash
SERVICES := auth admin gateway
PYTHON := python3
VENV := .venv

# Puertos por defecto
AUTH_PORT := 5001
ADMIN_PORT := 5002
GATEWAY_PORT := 8080

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
	@echo "    make install-gateway      - Instalar solo gateway"
	@echo ""
	@echo "  🚀 Gestión de Servicios:"
	@echo "    make start                - Iniciar todos los servicios"
	@echo "    make start-auth           - Iniciar solo auth-service"
	@echo "    make start-admin          - Iniciar solo admin-service"
	@echo "    make start-gateway        - Iniciar solo gateway"
	@echo ""
	@echo "  🔄 Control:"
	@echo "    make restart              - Reiniciar todos los servicios"
	@echo "    make restart-auth         - Reiniciar solo auth-service"
	@echo "    make restart-admin        - Reiniciar solo admin-service"
	@echo "    make restart-gateway      - Reiniciar solo gateway"
	@echo ""
	@echo "  🛑 Detener:"
	@echo "    make stop                 - Detener todos los servicios"
	@echo "    make stop-auth            - Detener solo auth-service"
	@echo "    make stop-admin           - Detener solo admin-service"
	@echo "    make stop-gateway         - Detener solo gateway"
	@echo ""
	@echo "  📊 Monitoreo:"
	@echo "    make status               - Ver estado de todos los servicios"
	@echo "    make logs                 - Ver logs de todos los servicios (últimas 50 líneas)"
	@echo "    make logs-auth            - Ver logs de auth-service"
	@echo "    make logs-admin           - Ver logs de admin-service"
	@echo "    make logs-gateway         - Ver logs de gateway"
	@echo "    make tail                 - Seguir logs en tiempo real (todos)"
	@echo "    make tail-auth            - Seguir logs de auth-service"
	@echo "    make tail-admin           - Seguir logs de admin-service"
	@echo "    make tail-gateway         - Seguir logs de gateway"
	@echo ""
	@echo "  🧪 Testing:"
	@echo "    make test                 - Ejecutar tests de todos los servicios"
	@echo "    make test-auth            - Ejecutar tests de auth-service"
	@echo "    make test-admin           - Ejecutar tests de admin-service"
	@echo "    make test-gateway         - Ejecutar tests de gateway"
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
install: install-auth install-admin install-gateway
	@echo "✓ Todas las dependencias instaladas"

install-auth:
	@echo "📦 Instalando auth-service..."
	@cd auth && $(MAKE) install

install-admin:
	@echo "📦 Instalando admin-service..."
	@cd admin && $(MAKE) install

install-gateway:
	@echo "📦 Instalando gateway..."
	@cd gateway && $(MAKE) install

# =============================================================================
# Iniciar Servicios
# =============================================================================
$(LOG_DIR):
	@mkdir -p $(LOG_DIR)

$(PID_DIR):
	@mkdir -p $(PID_DIR)

start: $(LOG_DIR) $(PID_DIR) start-auth wait-auth start-admin wait-admin start-gateway wait-gateway
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

start-gateway: $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Iniciando gateway en puerto $(GATEWAY_PORT)..."
	@cd gateway && \
		source $(VENV)/bin/activate && \
		PYTHONPATH=src FLASK_APP=gateway.app $(PYTHON) -m flask run \
			--host=0.0.0.0 --port=$(GATEWAY_PORT) --no-reload \
			> $(LOG_DIR)/gateway.log 2>&1 & \
		echo $$! > $(PID_DIR)/gateway.pid
	@echo "  PID: $$(cat $(PID_DIR)/gateway.pid)"

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

# =============================================================================
# Detener Servicios
# =============================================================================
stop: stop-gateway stop-admin stop-auth
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

# =============================================================================
# Reiniciar Servicios
# =============================================================================
restart: stop start

restart-auth: stop-auth start-auth wait-auth
	@echo "✓ Auth-service reiniciado"

restart-admin: stop-admin start-admin wait-admin
	@echo "✓ Admin-service reiniciado"

restart-gateway: stop-gateway start-gateway wait-gateway
	@echo "✓ Gateway reiniciado"

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
	@echo "  Logs - gateway"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@tail -n 50 $(LOG_DIR)/gateway.log 2>/dev/null || echo "  (sin logs)"

logs-auth:
	@tail -n 100 $(LOG_DIR)/auth.log 2>/dev/null || echo "Sin logs de auth-service"

logs-admin:
	@tail -n 100 $(LOG_DIR)/admin.log 2>/dev/null || echo "Sin logs de admin-service"

logs-gateway:
	@tail -n 100 $(LOG_DIR)/gateway.log 2>/dev/null || echo "Sin logs de gateway"

tail:
	@tail -f $(LOG_DIR)/*.log

tail-auth:
	@tail -f $(LOG_DIR)/auth.log

tail-admin:
	@tail -f $(LOG_DIR)/admin.log

tail-gateway:
	@tail -f $(LOG_DIR)/gateway.log

# =============================================================================
# Testing
# =============================================================================
test: test-auth test-admin test-gateway
	@echo "✓ Todos los tests completados"

test-auth:
	@echo "🧪 Ejecutando tests de auth-service..."
	@cd auth && ./test_auth_service.sh

test-admin:
	@echo "🧪 Ejecutando tests de admin-service..."
	@cd admin && ./test_admin_service.sh

test-gateway:
	@echo "🧪 Ejecutando tests de gateway..."
	@cd gateway && ./test_gateway.sh

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
