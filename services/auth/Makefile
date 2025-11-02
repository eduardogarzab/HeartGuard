PYTHON ?= python
VENV ?= .venv
BIN := $(VENV)/bin
export PYTHONPATH := src

.PHONY: install dev lint test clean

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt

DevEnv := FLASK_DEBUG=1 FLASK_ENV=development

dev: install
	$(DevEnv) $(BIN)/flask run --host=127.0.0.1 --port=5001 --reload

lint: install
	$(BIN)/python -m compileall src

test: install
	$(BIN)/pytest -q

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
