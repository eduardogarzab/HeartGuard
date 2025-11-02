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

dev: install
	FLASK_DEBUG=1 $(BIN)/flask run --reload

lint: install
	$(BIN)/python -m compileall src

test: install
	$(BIN)/pytest -q

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
