#!/bin/bash
set -e

# Wait for PostgreSQL to accept connections
if [ -n "$DB_HOST" ]; then
  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT:-5432}..."
  until nc -z "$DB_HOST" "${DB_PORT:-5432}"; do
    sleep 1
  done
  echo "PostgreSQL is ready."
fi

# Verify all external services are reachable before proceeding
echo "Checking external service health..."
uv run python manage.py check_services

# Run migrations
echo "Applying database migrations..."
uv run python manage.py migrate --noinput

# Seed reference data (idempotent - uses get_or_create)
echo "Seeding job categories and experience levels..."
uv run python manage.py seed_job_data

# Reset any analyses stuck in processing states from a previous interrupted run
echo "Resetting stuck analyses..."
uv run python manage.py reset_stuck_analyses

# Execute the container CMD (e.g. runserver, rqworker, etc.)
exec "$@"
