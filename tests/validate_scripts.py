# ABOUTME: Validates the lab shell scripts: bash syntax, shebang, ABOUTME header, executable bit.
# ABOUTME: Runs `bash -n` only, so no script is executed and no cluster or cloud account is needed.

import os
import subprocess
from pathlib import Path

import pytest

from tests.conftest import EXCLUDED_PATTERNS

REPO_ROOT = Path(__file__).parent.parent

# The scripts the labs and contributors run by hand. Listed explicitly so a deleted or renamed
# script fails here instead of silently dropping out of the parametrized set.
EXPECTED_SCRIPTS = [
    "labs/00-setup/setup.sh",
    "labs/00-setup/verify.sh",
    "labs/00-setup/teardown.sh",
    "labs/optional/aks-gpu-cluster/aks-setup.sh",
    "labs/optional/gke-gpu-cluster/gke-setup.sh",
    "scripts/test.sh",
]


def _shell_scripts() -> list[Path]:
    excluded = [*EXCLUDED_PATTERNS, ".venv/"]
    scripts = []
    for script in sorted(REPO_ROOT.rglob("*.sh")):
        rel = str(script.relative_to(REPO_ROOT))
        if not any(pattern in rel for pattern in excluded):
            scripts.append(script)
    return scripts


SHELL_SCRIPTS = _shell_scripts()


def _ids(scripts: list[Path]) -> list[str]:
    return [str(s.relative_to(REPO_ROOT)) for s in scripts]


@pytest.mark.parametrize("rel_path", EXPECTED_SCRIPTS)
def test_expected_script_exists(repo_root: Path, rel_path: str) -> None:
    """Every script the lab READMEs and contributor docs reference must exist."""
    assert (repo_root / rel_path).is_file(), f"Missing script: {rel_path}"


@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=_ids(SHELL_SCRIPTS))
def test_script_bash_syntax(script: Path) -> None:
    """`bash -n` parses the script without executing it."""
    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"bash -n failed:\n{result.stderr}"


@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=_ids(SHELL_SCRIPTS))
def test_script_has_bash_shebang(script: Path) -> None:
    """Scripts use bash features, so they must declare bash, not sh."""
    first_line = script.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env bash", f"Unexpected shebang: {first_line!r}"


@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=_ids(SHELL_SCRIPTS))
def test_script_has_aboutme_header(script: Path) -> None:
    """AGENTS.md requires a 2-line ABOUTME comment at the top of every code file."""
    lines = script.read_text().splitlines()
    assert lines[1].startswith("# ABOUTME: "), "Line 2 must be an ABOUTME comment"
    assert lines[2].startswith("# ABOUTME: "), "Line 3 must be an ABOUTME comment"


@pytest.mark.parametrize("script", SHELL_SCRIPTS, ids=_ids(SHELL_SCRIPTS))
def test_script_is_executable(script: Path) -> None:
    """Lab 00 runs its scripts as ./setup.sh and friends, which needs the executable bit."""
    assert os.access(script, os.X_OK), "Script is not executable (chmod +x)"
