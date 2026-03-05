#!/bin/sh
set -e

echo "==> Waiting for postgres..."
until python -c "import psycopg; psycopg.connect('host=$POSTGRES_HOST dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD')" 2>/dev/null; do
  sleep 1
done

echo "==> Apply migrations"
python manage.py migrate --noinput

echo "==> Run server"
exec python manage.py runserver 0.0.0.0:8000
