# ABOUTME: Validates that ruff lint, ruff format, and mypy pass on the test sources.
# ABOUTME: These commands are advertised in CLAUDE.md and must succeed on a clean checkout.

import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ruff_check_passes(repo_root: Path) -> None:
    """`uv run ruff check .` must exit 0 — no lint errors anywhere in the repo."""
    result = _run(["uv", "run", "ruff", "check", "."], cwd=repo_root)
    assert result.returncode == 0, (
        f"ruff check failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_ruff_format_check_passes(repo_root: Path) -> None:
    """`uv run ruff format --check .` must exit 0 — formatting is clean."""
    result = _run(["uv", "run", "ruff", "format", "--check", "."], cwd=repo_root)
    assert result.returncode == 0, (
        f"ruff format --check failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_mypy_passes_on_tests(repo_root: Path) -> None:
    """`uv run mypy tests/` must exit 0 — type checks pass on the test harness."""
    result = _run(["uv", "run", "mypy", "tests/"], cwd=repo_root)
    assert result.returncode == 0, (
        f"mypy failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
