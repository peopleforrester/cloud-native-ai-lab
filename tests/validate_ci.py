# ABOUTME: Validates the GitHub Actions test workflow has hardened defaults.
# ABOUTME: Pins actions to commit SHAs, runs lint gates, and limits permissions/runtime.

import re
from pathlib import Path

import yaml


def _load_workflow(repo_root: Path) -> dict:
    workflow_path = repo_root / ".github" / "workflows" / "test.yml"
    assert workflow_path.exists(), f"Missing CI workflow at {workflow_path}"
    with open(workflow_path) as f:
        return yaml.safe_load(f)


def test_workflow_has_minimal_permissions(repo_root: Path) -> None:
    """Workflow must declare top-level permissions: contents: read."""
    workflow = _load_workflow(repo_root)
    perms = workflow.get("permissions")
    assert perms is not None, "Workflow missing top-level permissions: block"
    assert perms.get("contents") == "read", (
        f"Workflow permissions.contents must be 'read', got {perms!r}"
    )


def test_workflow_has_concurrency(repo_root: Path) -> None:
    """Workflow must define concurrency to cancel superseded runs."""
    workflow = _load_workflow(repo_root)
    concurrency = workflow.get("concurrency")
    assert concurrency is not None, "Workflow missing concurrency: block"
    assert concurrency.get("cancel-in-progress") is True, (
        "concurrency.cancel-in-progress must be true to save runner minutes"
    )


def test_test_job_has_timeout(repo_root: Path) -> None:
    """The test job must declare timeout-minutes to prevent runaway runs."""
    workflow = _load_workflow(repo_root)
    job = workflow.get("jobs", {}).get("test", {})
    timeout = job.get("timeout-minutes")
    assert isinstance(timeout, int) and timeout > 0, (
        f"jobs.test.timeout-minutes must be a positive integer, got {timeout!r}"
    )


def test_workflow_runs_lint_gates(repo_root: Path) -> None:
    """Workflow must run ruff check, ruff format --check, and mypy as explicit gates."""
    workflow = _load_workflow(repo_root)
    steps = workflow.get("jobs", {}).get("test", {}).get("steps", [])
    run_lines = " ".join(step.get("run", "") for step in steps if "run" in step)
    assert "ruff check" in run_lines, "Workflow must run 'ruff check'"
    assert "ruff format --check" in run_lines, "Workflow must run 'ruff format --check'"
    assert "mypy" in run_lines, "Workflow must run 'mypy' as an explicit fail-fast gate"


def test_checkout_disables_credential_persistence(repo_root: Path) -> None:
    """actions/checkout must set persist-credentials: false — this CI never pushes,
    so leaving the GITHUB_TOKEN in .git/config is needless credential exposure."""
    workflow = _load_workflow(repo_root)
    steps = workflow.get("jobs", {}).get("test", {}).get("steps", [])
    checkout = next(
        (s for s in steps if isinstance(s.get("uses"), str) and "actions/checkout@" in s["uses"]),
        None,
    )
    assert checkout is not None, "Workflow must use actions/checkout"
    assert checkout.get("with", {}).get("persist-credentials") is False, (
        "actions/checkout must set with.persist-credentials: false"
    )


def test_actions_pinned_to_commit_sha(repo_root: Path) -> None:
    """Third-party actions must be pinned to 40-char commit SHAs, not tags."""
    workflow_path = repo_root / ".github" / "workflows" / "test.yml"
    raw = workflow_path.read_text()

    uses_lines = [
        line.strip().lstrip("-").strip()
        for line in raw.splitlines()
        if line.strip().lstrip("-").strip().startswith("uses:")
    ]
    # Only third-party actions need SHA pinning. Local actions (`uses: ./...`)
    # are checked out with the repo and carry no supply-chain risk.
    third_party = [line for line in uses_lines if not re.match(r"^uses:\s+\./", line)]
    sha_pattern = re.compile(r"^uses:\s+\S+@[0-9a-f]{40}\b")

    bad = [line for line in third_party if not sha_pattern.match(line)]
    assert not bad, "Actions must be pinned to 40-char commit SHAs:\n" + "\n".join(bad)
