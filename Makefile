SHELL := /bin/sh

.PHONY: up down logs bot migrate-gen migrate-up migrate test lint

MIGRATIONS_DIR := $(CURDIR)/src/infrastructure/database/migrations/versions


build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

bot:
	docker compose up -d bot

migrate-gen:
	mkdir "$(MIGRATIONS_DIR)" 2>nul || exit 0
	docker compose run --rm --build -v "$(MIGRATIONS_DIR)":/app/src/infrastructure/database/migrations/versions bot alembic revision --autogenerate

migrate-up:
	docker compose run --rm --build bot alembic upgrade head

migrate: migrate-gen migrate-up

test:
	docker compose run --rm --build bot pytest

lint:
	docker compose run --rm --build bot mypy src
