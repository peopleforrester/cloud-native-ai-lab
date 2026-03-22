# ABOUTME: Validates that all YAML files in the repository parse without errors.
# ABOUTME: Catches syntax issues in Kubernetes manifests and configuration files.

from pathlib import Path

import pytest
import yaml


def test_all_yaml_files_parse(all_yaml_files: list[Path]) -> None:
    """Every YAML file in the repo must be valid YAML."""
    errors = []
    for yaml_file in all_yaml_files:
        try:
            with open(yaml_file) as f:
                list(yaml.safe_load_all(f))
        except yaml.YAMLError as e:
            errors.append(f"{yaml_file}: {e}")

    assert not errors, "YAML parsing errors:\n" + "\n".join(errors)


def test_yaml_files_exist(all_yaml_files: list[Path]) -> None:
    """At least one YAML file should exist (sanity check)."""
    assert len(all_yaml_files) > 0, "No YAML files found in repository"
