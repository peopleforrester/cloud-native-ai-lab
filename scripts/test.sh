#!/usr/bin/env bash
# ABOUTME: Single entry point for running the full test suite.
# ABOUTME: Uses uv to manage dependencies and runs pytest with verbose output.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Cloud Native AI Lab Test Suite ==="
echo ""

# Ensure dependencies are installed
echo "Syncing dependencies..."
uv sync --dev --quiet

echo "Running tests..."
echo ""

cd "${REPO_ROOT}"
uv run pytest tests/ -v --tb=short "$@"
