#!/usr/bin/env bash
# Run all unit tests
set -e
cd "$(dirname "$0")"
uv run python manage.py test tests.unit --verbosity=2
