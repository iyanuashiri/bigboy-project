#!/bin/sh
set -e

echo "Running migrations..."
uv run python manage.py migrate

echo "Starting Celery worker..."
uv run celery -A config.celery worker --loglevel=info --pool=solo --concurrency="${CELERY_CONCURRENCY:-1}" &

echo "Starting server..."
exec uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2
