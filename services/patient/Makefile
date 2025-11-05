.PHONY: install dev test clean

install:
	pip install -r requirements.txt

dev:
	python -m flask --app src.patient.app run --port 5004 --reload

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
