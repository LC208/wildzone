#!/bin/sh

echo "Apply migrations"
uv run python manage.py migrate

echo "Run server"
uv run python manage.py runserver 0.0.0.0:8000
