# =============================================================================
# Admin Service - Makefile
# =============================================================================
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
PORT := 5002

export PYTHONPATH := src

.PHONY: help install dev test clean

help:
	@echo "Admin Service - Comandos disponibles:"
	@echo "  make install    - Instalar dependencias"
	@echo "  make dev        - Ejecutar en modo desarrollo"
	@echo "  make test       - Ejecutar suite de pruebas"
	@echo "  make clean      - Limpiar archivos temporales"

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	@echo "📦 Instalando dependencias de admin-service..."
	@$(BIN)/pip install --upgrade pip -q
	@$(BIN)/pip install -r requirements.txt -q
	@echo "✓ Dependencias instaladas"

dev: install
	@echo "🚀 Iniciando admin-service en modo desarrollo (puerto $(PORT))..."
	@FLASK_DEBUG=1 FLASK_APP=admin.app $(BIN)/flask run --host=0.0.0.0 --port=$(PORT) --reload

test: install
	@echo "🧪 Ejecutando tests de admin-service..."
	@./test_admin_service.sh

clean:
	@echo "🧹 Limpiando admin-service..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Limpieza completada"
