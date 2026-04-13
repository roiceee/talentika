#!/usr/bin/env bash
# Run all integration tests
set -e
cd "$(dirname "$0")"
uv run python manage.py test tests.integration --verbosity=2
