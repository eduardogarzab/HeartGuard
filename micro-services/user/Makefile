PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: install dev test clean

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	@echo "📦 Instalando dependencias de user-service..."
	@$(BIN)/pip install --upgrade pip -q
	@$(BIN)/pip install -r requirements.txt -q
	@echo "✓ Dependencias instaladas"

dev: install
	@echo "🚀 Iniciando user-service en modo desarrollo (puerto 5003)..."
	@FLASK_DEBUG=1 FLASK_APP=src.user.app $(BIN)/flask run --host=0.0.0.0 --port=5003 --reload

test: install
	@$(BIN)/pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
