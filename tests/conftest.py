# ABOUTME: Shared pytest fixtures for the cloud-native-ai-lab test suite.
# ABOUTME: Provides repo root path and helper functions for file discovery.

from pathlib import Path

import pytest

# Directories that live in the working tree but are never published: gitignored
# local archives and transcripts that may carry client, employer, or third-party
# personal information. Content gates must not read or grade them.
LOCAL_ONLY_PATTERNS = [
    "claude-ai-context",
    "transcripts",
]

EXCLUDED_PATTERNS = [
    "compass_artifact",
    "node_modules",
    "__pycache__",
    ".git/",
    *LOCAL_ONLY_PATTERNS,
]


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def all_markdown_files(repo_root: Path) -> list[Path]:
    """Return all markdown files in the repo, excluding source material originals."""
    excluded_patterns = EXCLUDED_PATTERNS
    files = []
    for md_file in repo_root.rglob("*.md"):
        rel = str(md_file.relative_to(repo_root))
        if not any(pattern in rel for pattern in excluded_patterns):
            files.append(md_file)
    return files


@pytest.fixture
def all_yaml_files(repo_root: Path) -> list[Path]:
    """Return all YAML files in the repo."""
    files = []
    for pattern in ["*.yaml", "*.yml"]:
        for yaml_file in repo_root.rglob(pattern):
            rel = str(yaml_file.relative_to(repo_root))
            if ".git/" not in rel:
                files.append(yaml_file)
    return files


@pytest.fixture
def docs_markdown_files(repo_root: Path) -> list[Path]:
    """Return markdown files under docs/ that are final content (not source originals)."""
    excluded_patterns = EXCLUDED_PATTERNS
    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        return []
    files = []
    for md_file in docs_dir.rglob("*.md"):
        rel = str(md_file.relative_to(repo_root))
        if not any(pattern in rel for pattern in excluded_patterns):
            files.append(md_file)
    return files
