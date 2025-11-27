.PHONY: help install run test clean dev docker-build docker-run

PYTHON := python3
VENV := .venv

help:
	@echo "HeartGuard AI Prediction Service - Makefile"
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make install       - Instala dependencias"
	@echo "  make run           - Ejecuta el servicio"
	@echo "  make dev           - Ejecuta en modo desarrollo"
	@echo "  make test          - Ejecuta pruebas"
	@echo "  make clean         - Limpia archivos temporales"
	@echo "  make docker-build  - Construye imagen Docker"
	@echo "  make docker-run    - Ejecuta en Docker"

install:
	@echo "📦 Instalando dependencias de ai-prediction..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "  Creando entorno virtual..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "  Instalando paquetes..."
	@$(VENV)/bin/pip install --upgrade pip > /dev/null 2>&1
	@$(VENV)/bin/pip install -r requirements.txt > /dev/null 2>&1
	@echo "  ✓ Dependencias instaladas"

run:
	@source $(VENV)/bin/activate && PYTHONPATH=src python -m src.app

dev:
	@source $(VENV)/bin/activate && FLASK_DEBUG=True PYTHONPATH=src python -m src.app

test:
	@if [ -d tests ]; then \
		source $(VENV)/bin/activate && pytest tests/ -v; \
	else \
		echo "⚠️  No hay tests definidos"; \
	fi

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

docker-build:
	docker build -t heartguard-ai-prediction:latest .

docker-run:
	docker run -p 5007:5007 heartguard-ai-prediction:latest
