# ABOUTME: Validates that internal markdown links resolve to existing files.
# ABOUTME: Checks relative links in all markdown files against the filesystem.

import re
from pathlib import Path
from urllib.parse import unquote

import pytest


def test_internal_links_resolve(all_markdown_files: list[Path], repo_root: Path) -> None:
    """All relative markdown links should point to files that exist."""
    broken_links = []

    for md_file in all_markdown_files:
        content = md_file.read_text()
        # Match [text](path) but not [text](http...) or [text](#anchor)
        links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", content)

        for link_text, link_target in links:
            # Skip external URLs and anchors
            if link_target.startswith(("http://", "https://", "#", "mailto:")):
                continue

            # Strip anchor from link
            target_path = link_target.split("#")[0]
            if not target_path:
                continue

            target_path = unquote(target_path)

            # Resolve relative to the markdown file's directory
            resolved = (md_file.parent / target_path).resolve()

            if not resolved.exists():
                rel_md = md_file.relative_to(repo_root)
                broken_links.append(f"{rel_md}: [{link_text}]({link_target})")

    assert not broken_links, "Broken internal links:\n" + "\n".join(broken_links)
