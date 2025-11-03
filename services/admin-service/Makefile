.PHONY: install run lint format test

install:
python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

run:
flask --app src.admin_service.app:create_app --debug run

lint:
flake8 src

format:
black src tests

test:
pytest
