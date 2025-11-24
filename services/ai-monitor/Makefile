.PHONY: help install dev run test clean docker-build docker-run

PYTHON := python3
VENV := .venv

help:
	@echo "AI Monitor Service - Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run in development mode"
	@echo "  make run          - Run the monitor worker"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"

install:
	@echo "📦 Instalando dependencias de ai-monitor..."
	@if [ ! -d "$(VENV)" ]; then \
		echo "  Creando entorno virtual..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "  Instalando paquetes..."
	@$(VENV)/bin/pip install --upgrade pip > /dev/null 2>&1
	@$(VENV)/bin/pip install -r requirements.txt > /dev/null 2>&1
	@echo "  ✓ Dependencias instaladas"

dev:
	@echo "Starting AI Monitor in development mode..."
	@source $(VENV)/bin/activate && python -m src.app

run: dev

test:
	@if [ -d tests ]; then \
		source $(VENV)/bin/activate && python -m pytest tests/ -v; \
	else \
		echo "⚠️  No hay tests definidos"; \
	fi

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

docker-build:
	docker build -t heartguard-ai-monitor:latest .

docker-run:
	docker run --rm \
		--env-file .env \
		--name ai-monitor \
		heartguard-ai-monitor:latest
