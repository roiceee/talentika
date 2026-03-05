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

# Run migrations
echo "Applying database migrations..."
uv run python manage.py migrate --noinput

# Execute the container CMD (e.g. runserver, rqworker, etc.)
exec "$@"
