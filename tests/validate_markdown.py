# ABOUTME: Validates markdown files for common structural issues.
# ABOUTME: Checks for broken heading hierarchy and empty files.

import re
from pathlib import Path

import pytest


def test_no_empty_markdown_files(all_markdown_files: list[Path]) -> None:
    """No markdown file should be empty."""
    empty_files = []
    for md_file in all_markdown_files:
        content = md_file.read_text().strip()
        if not content:
            empty_files.append(str(md_file))

    assert not empty_files, "Empty markdown files:\n" + "\n".join(empty_files)


def test_markdown_files_have_h1(all_markdown_files: list[Path]) -> None:
    """Every markdown file should have at least one H1 heading."""
    missing_h1 = []
    for md_file in all_markdown_files:
        content = md_file.read_text()
        if not re.search(r"^# ", content, re.MULTILINE):
            missing_h1.append(str(md_file))

    assert not missing_h1, "Markdown files missing H1 heading:\n" + "\n".join(missing_h1)


def test_no_broken_heading_hierarchy(all_markdown_files: list[Path]) -> None:
    """Headings should not skip levels (e.g., H1 directly to H3)."""
    issues = []
    for md_file in all_markdown_files:
        content = md_file.read_text()
        headings = re.findall(r"^(#{1,6}) ", content, re.MULTILINE)
        if not headings:
            continue

        prev_level = 0
        for heading in headings:
            level = len(heading)
            if prev_level > 0 and level > prev_level + 1:
                issues.append(
                    f"{md_file}: heading jumps from H{prev_level} to H{level}"
                )
                break
            prev_level = level

    assert not issues, "Broken heading hierarchy:\n" + "\n".join(issues)
