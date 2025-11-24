.PHONY: help install dev run test clean docker-build docker-run

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
	pip install -r requirements.txt

dev:
	@echo "Starting AI Monitor in development mode..."
	python src/monitor.py

run: dev

test:
	@echo "Running tests..."
	python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete

docker-build:
	docker build -t heartguard-ai-monitor:latest .

docker-run:
	docker run --rm \
		--env-file .env \
		--name ai-monitor \
		heartguard-ai-monitor:latest
