# ABOUTME: End-to-end run of the labs on a real kind cluster: create it, install, apply manifests.
# ABOUTME: Needs kind, kubectl, helm and a reachable Docker daemon; fails loudly without them.

import os
import shlex
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.e2e.lab_plan import KIND_CONFIG, LABS, Lab, manifest_commands

# Its own name, not the lab's `ai-workshop`, so the suite never reuses or deletes a learner's
# cluster on the same host. The node image, port mappings and labels still come from the lab file.
CLUSTER_NAME = "cnai-lab-e2e"
REQUIRED_TOOLS = ("docker", "kind", "kubectl", "helm")
COMMAND_TIMEOUT_SECONDS = 900


def _run(argv: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )


def _describe(command: str, result: subprocess.CompletedProcess[str]) -> str:
    return (
        f"$ {command}\nexit {result.returncode}\n"
        f"--- stdout\n{result.stdout.strip()}\n--- stderr\n{result.stderr.strip()}"
    )


@pytest.fixture(scope="session")
def tools() -> None:
    """Fail every test up front, naming what is missing, when the gate host cannot run kind."""
    missing = [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
    if missing:
        pytest.fail(
            "The kind-cluster E2E needs kind, kubectl, helm and docker on PATH. "
            f"Missing: {', '.join(missing)}",
            pytrace=False,
        )
    info = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
    if info.returncode != 0:
        pytest.fail(
            "The kind-cluster E2E needs a Docker daemon this user can reach, and "
            f"`docker info` failed:\n{info.stderr.strip()}",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def cluster_env(tools: None, tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, str]]:
    """Create the lab cluster from labs/00-setup/kind-cluster.yaml and delete it afterwards.

    kubectl and helm get a kubeconfig and Helm home of their own under the pytest temp dir, so
    the run neither switches the user's current context nor adds repos to their Helm config.
    """
    home = tmp_path_factory.mktemp("kind-e2e")
    kubeconfig = home / "kubeconfig"
    env = {
        **os.environ,
        "KUBECONFIG": str(kubeconfig),
        "HELM_CACHE_HOME": str(home / "helm-cache"),
        "HELM_CONFIG_HOME": str(home / "helm-config"),
        "HELM_DATA_HOME": str(home / "helm-data"),
    }
    existing = _run(["kind", "get", "clusters"], env, home)
    if CLUSTER_NAME in existing.stdout.split():
        pytest.fail(
            f"A kind cluster named {CLUSTER_NAME} already exists, probably from an interrupted run. "
            f"Delete it with `kind delete cluster --name {CLUSTER_NAME}` and run again.",
            pytrace=False,
        )
    argv = ["kind", "create", "cluster", "--config", str(KIND_CONFIG), "--name", CLUSTER_NAME]
    argv += ["--kubeconfig", str(kubeconfig), "--wait", "300s"]
    create = shlex.join(argv)
    result = _run(argv, env, home)
    if result.returncode != 0:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME], env, home)
        pytest.fail(
            f"Could not create the lab cluster.\n{_describe(create, result)}", pytrace=False
        )
    try:
        yield env
    finally:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME], env, home)


def test_cluster_matches_lab_00(cluster_env: dict[str, str]) -> None:
    """Lab 00 promises three Ready nodes: one control plane and two labelled simulated-GPU workers."""
    zones = [
        "kubectl",
        "get",
        "nodes",
        "-l",
        "node.kubernetes.io/gpu-type=simulated",
        "-o",
        r"jsonpath={.items[*].metadata.labels.topology\.kubernetes\.io/zone}",
    ]
    command = shlex.join(zones)
    result = _run(zones, cluster_env, KIND_CONFIG.parent)
    assert result.returncode == 0, _describe(command, result)
    assert sorted(result.stdout.split()) == ["zone-a", "zone-b"], _describe(command, result)
    wait = "kubectl wait --for=condition=Ready nodes --all --timeout=300s"
    ready = _run(shlex.split(wait), cluster_env, KIND_CONFIG.parent)
    assert ready.returncode == 0, _describe(wait, ready)
    assert ready.stdout.count("condition met") == 3, _describe(wait, ready)


# Labs run in order on one cluster, as a learner works through them: lab 03 queues a JobSet
# through the Kueue LocalQueue that lab 01 created.
@pytest.mark.parametrize("lab", LABS, ids=[lab.name for lab in LABS])
def test_lab_installs_and_applies(cluster_env: dict[str, str], lab: Lab) -> None:
    """Install the lab's controllers at their pinned versions, then apply all of its manifests/.

    An install failure stops the lab, since nothing after it can apply. Apply failures are
    collected so one run reports every manifest the API server rejects.
    """
    for command in lab.install:
        result = _run(shlex.split(command), cluster_env, lab.path)
        assert result.returncode == 0, (
            f"Lab {lab.name}: install step failed.\n{_describe(command, result)}"
        )
    failures: list[str] = []
    for command in manifest_commands(lab):
        result = _run(shlex.split(command), cluster_env, lab.path)
        if result.returncode != 0:
            failures.append(_describe(command, result))
    assert not failures, f"Lab {lab.name}: manifests rejected.\n\n" + "\n\n".join(failures)
