.PHONY: setup up down migrate revision test lint check logs

setup:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

up:
	docker compose up --build

down:
	docker compose down

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(message)"

test:
	pytest

lint:
	ruff check app tests
	ruff format --check app tests
	mypy app

check: lint test

logs:
	docker compose logs -f

