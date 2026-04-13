#!/usr/bin/env bash
# Run all integration tests
set -e
cd "$(dirname "$0")"
uv run pytest tests/integration/ -v --tb=short 2>&1 | python3 format_test_output.py
