#!/usr/bin/env bash
# Run all unit tests
set -e
cd "$(dirname "$0")"
uv run pytest tests/unit/ -v --tb=short 2>&1 | sed 's|[^ ]*\.py::||g'
