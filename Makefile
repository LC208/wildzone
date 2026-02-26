.PHONY: build up down logs migrate superuser

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend uv run python manage.py migrate

superuser:
	docker compose exec backend uv run python manage.py createsuperuser

dev: build up
