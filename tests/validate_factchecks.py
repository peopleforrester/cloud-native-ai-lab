# ABOUTME: Validates that the 5 mandatory fact-check corrections are applied across all docs.
# ABOUTME: Checks for incorrect values and ensures correct values appear at least once.

import re
from pathlib import Path

import pytest


def _read_content_files(repo_root: Path) -> list[tuple[Path, str]]:
    """Read all final content markdown files (excluding source originals and tests)."""
    excluded_patterns = ["compass_artifact", "node_modules", "__pycache__", ".git/"]
    results = []
    for md_file in repo_root.rglob("*.md"):
        rel = str(md_file.relative_to(repo_root))
        if not any(pattern in rel for pattern in excluded_patterns):
            results.append((md_file, md_file.read_text()))
    return results


class TestJobSetVersion:
    """JobSet version must be v0.11.1, not v0.10.1."""

    def test_no_incorrect_jobset_version(self, repo_root: Path) -> None:
        """The incorrect JobSet version v0.10.1 should not appear in any content file."""
        for md_file, content in _read_content_files(repo_root):
            # Only flag v0.10.1 when it appears near "JobSet" context
            if "v0.10.1" in content and "jobset" in content.lower():
                rel = md_file.relative_to(repo_root)
                pytest.fail(
                    f"{rel} contains incorrect JobSet version v0.10.1 "
                    f"(should be v0.11.1)"
                )

    def test_correct_jobset_version_exists(self, repo_root: Path) -> None:
        """The correct JobSet version v0.11.1 must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "v0.11.1" in content:
                return
        pytest.fail("Correct JobSet version v0.11.1 not found in any content file")


class TestMCPServerCount:
    """MCP server count must be 10,000+, not 6,400."""

    def test_no_incorrect_mcp_count(self, repo_root: Path) -> None:
        """The incorrect MCP server count 6,400 should not appear in content files."""
        for md_file, content in _read_content_files(repo_root):
            if "6,400" in content or "6400" in content:
                rel = md_file.relative_to(repo_root)
                pytest.fail(
                    f"{rel} contains incorrect MCP server count 6,400 "
                    f"(should be 10,000+)"
                )

    def test_correct_mcp_count_exists(self, repo_root: Path) -> None:
        """The correct MCP server count 10,000+ must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "10,000" in content or "10000" in content:
                return
        pytest.fail("Correct MCP server count 10,000+ not found in any content file")


class TestInferenceObjective:
    """InferenceModel was renamed to InferenceObjective in GA/v1."""

    def test_no_inferencemodel_in_ga_context(self, repo_root: Path) -> None:
        """InferenceModel should not appear as a current GA CRD name.

        Note: It's acceptable to mention InferenceModel in historical context
        (e.g., 'renamed from InferenceModel'), so we check for patterns that
        present it as the current name.
        """
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            # Skip the fact-check source document itself
            if "compass_artifact" in rel:
                continue
            # Check for InferenceModel used as a current CRD name
            # Allow mentions in historical/rename context
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "InferenceModel" in line:
                    # Allow if it's in a rename/migration context
                    lower_line = line.lower()
                    rename_context = any(
                        word in lower_line
                        for word in ["renamed", "was renamed", "previously", "formerly",
                                     "migration", "replaced", "old name", "not inferencemodel"]
                    )
                    if not rename_context:
                        pytest.fail(
                            f"{rel}:{i} uses 'InferenceModel' as current CRD name "
                            f"(should be 'InferenceObjective' for GA/v1)"
                        )

    def test_correct_inference_objective_exists(self, repo_root: Path) -> None:
        """InferenceObjective must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "InferenceObjective" in content:
                return
        pytest.fail("InferenceObjective not found in any content file")


class TestGenAIStatQualifier:
    """The 66% gen AI stat must include its qualifier wherever it appears."""

    def test_66_percent_has_qualifier(self, repo_root: Path) -> None:
        """When 66% appears with gen AI context, it should have the qualifier."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            # Skip the fact-check doc
            if "compass_artifact" in rel:
                continue
            # Look for "66%" near gen AI / generative AI context
            matches = list(re.finditer(r"66\s*%", content))
            for match in matches:
                # Get surrounding context (200 chars each direction)
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end].lower()
                if any(term in context for term in ["generative ai", "gen ai", "genai"]):
                    # Check for qualifier
                    has_qualifier = any(
                        phrase in context
                        for phrase in [
                            "hosting generative ai models",
                            "host generative ai models",
                            "organizations already hosting",
                            "organizations that host",
                            "orgs hosting",
                        ]
                    )
                    if not has_qualifier:
                        pytest.fail(
                            f"{rel} uses 66% gen AI stat without qualifier. "
                            f"Must specify 'of organizations already hosting "
                            f"generative AI models'"
                        )


class TestLlmdAttribution:
    """llm-d must be attributed as launched by Red Hat, not co-created equally."""

    def test_llmd_red_hat_attribution(self, repo_root: Path) -> None:
        """When llm-d is mentioned with contributors, Red Hat must be the launcher."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            if "compass_artifact" in rel:
                continue
            lower = content.lower()
            if "llm-d" not in lower:
                continue
            # If the file mentions llm-d with multiple companies, check attribution
            if "co-created" in lower or "co-built" in lower:
                # Check if Red Hat is distinguished
                if "red hat" not in lower:
                    pytest.fail(
                        f"{rel} describes llm-d as 'co-created/co-built' without "
                        f"distinguishing Red Hat as the project launcher"
                    )
