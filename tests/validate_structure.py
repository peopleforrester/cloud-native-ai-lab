# ABOUTME: Validates that all required files and directories exist in the repository.
# ABOUTME: Uses a manifest of expected paths as the source of truth for completeness.

from pathlib import Path

import pytest

# Required files for a complete repository
REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "checklist.md",
    ".github/CONTRIBUTING.md",
    "docs/landscape-report.md",
    "docs/talk-outline.md",
    "docs/projects/dra.md",
    "docs/projects/kueue.md",
    "docs/projects/jobset.md",
    "docs/projects/leaderworkerset.md",
    "docs/projects/kserve.md",
    "docs/projects/knative.md",
    "docs/projects/llm-d.md",
    "docs/projects/gateway-api-inference.md",
    "docs/projects/kagent.md",
    "docs/projects/mcp.md",
    "docs/projects/aaif.md",
    "labs/00-setup/README.md",
    "labs/00-setup/kind-cluster.yaml",
    "labs/01-kueue-basics/README.md",
    "labs/02-dra-resource-claims/README.md",
    "labs/03-jobset-training/README.md",
    "labs/04-kserve-inference/README.md",
    "labs/05-gateway-routing/README.md",
    "labs/06-kagent-mcp/README.md",
    "labs/optional/eks-gpu-cluster/README.md",
    "labs/optional/gke-gpu-cluster/README.md",
    "labs/optional/aks-gpu-cluster/README.md",
]

REQUIRED_DIRS = [
    "docs/projects",
    "labs/00-setup",
    "labs/01-kueue-basics/manifests",
    "labs/02-dra-resource-claims/manifests",
    "labs/03-jobset-training/manifests",
    "labs/04-kserve-inference/manifests",
    "labs/05-gateway-routing/manifests",
    "labs/06-kagent-mcp/manifests",
    "labs/optional/eks-gpu-cluster",
    "labs/optional/gke-gpu-cluster",
    "labs/optional/aks-gpu-cluster",
    ".github",
]


@pytest.mark.parametrize("file_path", REQUIRED_FILES)
def test_required_file_exists(repo_root: Path, file_path: str) -> None:
    """Each required file must exist in the repository."""
    full_path = repo_root / file_path
    assert full_path.exists(), f"Required file missing: {file_path}"


@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_required_directory_exists(repo_root: Path, dir_path: str) -> None:
    """Each required directory must exist in the repository."""
    full_path = repo_root / dir_path
    assert full_path.is_dir(), f"Required directory missing: {dir_path}"
