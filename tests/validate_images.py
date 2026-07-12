# ABOUTME: Validates that container images in Kubernetes manifests use pinned tags.
# ABOUTME: Bare `:latest` (or untagged) references break the project's image policy.

import re
from pathlib import Path

_IMAGE_RE = re.compile(r"^\s*image:\s*([^\s#]+)", re.MULTILINE)


def _iter_image_refs(yaml_files: list[Path]) -> list[tuple[Path, str]]:
    """Yield (file, image_ref) for every container image declared in any YAML file."""
    refs: list[tuple[Path, str]] = []
    for yaml_file in yaml_files:
        text = yaml_file.read_text()
        for match in _IMAGE_RE.finditer(text):
            refs.append((yaml_file, match.group(1).strip().strip('"').strip("'")))
    return refs


def test_no_latest_image_tags(all_yaml_files: list[Path], repo_root: Path) -> None:
    """No manifest may use `:latest` or omit the tag — pin every image."""
    bad: list[str] = []
    for yaml_file, image in _iter_image_refs(all_yaml_files):
        if image.endswith(":latest"):
            bad.append(f"{yaml_file.relative_to(repo_root)}: {image}")
            continue
        # Check tag presence: image must contain ':' after the last '/'
        # (otherwise Docker defaults to :latest).
        name_part = image.rsplit("/", 1)[-1]
        if ":" not in name_part and "@" not in name_part:
            bad.append(f"{yaml_file.relative_to(repo_root)}: {image} (no tag)")
    assert not bad, "Manifests with :latest or untagged images:\n" + "\n".join(bad)
