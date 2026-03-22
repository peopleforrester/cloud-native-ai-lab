#!/usr/bin/env bash
# ABOUTME: Single entry point for running the full test suite.
# ABOUTME: Installs dependencies and runs pytest with verbose output.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Cloud Native AI Lab Test Suite ==="
echo ""

# Create and activate virtualenv if needed
VENV_DIR="${REPO_ROOT}/.venv"
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}" || uv venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# Install dependencies if needed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install -q -r "${REPO_ROOT}/requirements-dev.txt" 2>/dev/null \
        || uv pip install -r "${REPO_ROOT}/requirements-dev.txt"
    echo ""
fi

echo "Running tests..."
echo ""

cd "${REPO_ROOT}"
python3 -m pytest tests/ -v --tb=short "$@"
