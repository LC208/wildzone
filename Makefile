include .env
export

.PHONY: build up down logs migrate superuser shell

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend python manage.py migrate

superuser:
	docker compose exec backend python manage.py createsuperuser

shell:
	docker compose exec backend python manage.py shell

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

dev: build up logs

db:
	docker compose exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)