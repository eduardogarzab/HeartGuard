# =============================================================================
# Media Service - Makefile
# =============================================================================
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
PORT := 5005

export PYTHONPATH := src

.PHONY: help install dev test lint clean

help:
	@echo "Media Service - Comandos disponibles:"
	@echo "  make install    - Instalar dependencias"
	@echo "  make dev        - Ejecutar en modo desarrollo"
	@echo "  make test       - Ejecutar pruebas unitarias"
	@echo "  make clean      - Limpiar artefactos temporales"

$(VENV):
	$(PYTHON) -m venv $(VENV)


install: $(VENV)
	@echo "📦 Instalando dependencias de media-service..."
	@$(BIN)/pip install --upgrade pip -q
	@$(BIN)/pip install -r requirements.txt -q
	@echo "✓ Dependencias instaladas"

dev: install
	@echo "🚀 Iniciando media-service en modo desarrollo (puerto $(PORT))..."
	@FLASK_DEBUG=1 FLASK_APP=media.app $(BIN)/flask run --host=0.0.0.0 --port=$(PORT) --reload

test: install
	@echo "🧪 Ejecutando tests de media-service..."
	@$(BIN)/pytest -q

clean:
	@echo "🧹 Limpiando media-service..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@echo "✓ Limpieza completada"
