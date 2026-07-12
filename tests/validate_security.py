# ABOUTME: Validates that at least one job manifest demonstrates pod-level securityContext.
# ABOUTME: Acts as a teaching anchor — if the example regresses, the test fails loudly.

from pathlib import Path

import yaml


def test_kueue_sample_job_uses_security_context(repo_root: Path) -> None:
    """labs/01-kueue-basics/manifests/sample-job.yaml must demonstrate runAsNonRoot,
    capability dropping, and a read-only root filesystem so learners absorb the
    pattern by osmosis."""
    manifest_path = repo_root / "labs" / "01-kueue-basics" / "manifests" / "sample-job.yaml"
    with open(manifest_path) as f:
        doc = yaml.safe_load(f)

    pod_spec = doc["spec"]["template"]["spec"]
    pod_sec = pod_spec.get("securityContext")
    assert pod_sec is not None, "Pod template missing securityContext block"
    assert pod_sec.get("runAsNonRoot") is True, "pod securityContext.runAsNonRoot must be true"
    assert pod_sec.get("runAsUser") == 65534, (
        "pod securityContext.runAsUser must pin a non-root UID (65534/nobody)"
    )
    seccomp = pod_sec.get("seccompProfile", {})
    assert seccomp.get("type") == "RuntimeDefault", (
        "pod securityContext.seccompProfile.type must be RuntimeDefault"
    )

    container = pod_spec["containers"][0]
    container_sec = container.get("securityContext")
    assert container_sec is not None, "Container missing securityContext block"
    assert container_sec.get("readOnlyRootFilesystem") is True, (
        "container securityContext.readOnlyRootFilesystem must be true"
    )
    assert container_sec.get("allowPrivilegeEscalation") is False, (
        "container securityContext.allowPrivilegeEscalation must be false"
    )

    capabilities = container_sec.get("capabilities", {})
    drops = capabilities.get("drop", [])
    assert "ALL" in drops, "container must drop ALL capabilities"
