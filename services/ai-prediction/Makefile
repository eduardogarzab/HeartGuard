.PHONY: help install run test clean dev docker-build docker-run

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
	pip install -r requirements.txt

run:
	python -m src.app

dev:
	FLASK_DEBUG=True python -m src.app

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

docker-build:
	docker build -t heartguard-ai-prediction:latest .

docker-run:
	docker run -p 5008:5008 heartguard-ai-prediction:latest
